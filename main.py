import argparse
import logging
import sys
import time
from typing import Optional

import cv2

from config import CONFIG
from src.camera.camera_manager import CameraManager
from src.controllers.mouse_controller import MouseController
from src.controllers.presentation_controller import PresentationController
from src.controllers.volume_controller import VolumeController
from src.safety.activation_manager import ActivationManager
from src.vision.gesture_recognizer import GestureRecognizer
from src.vision.hand_tracker import HandTracker


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class DesktopGestureApp:
    def __init__(self) -> None:
        self.camera = CameraManager(
            index=CONFIG.camera.index,
            width=CONFIG.camera.width,
            height=CONFIG.camera.height,
            fps=CONFIG.camera.fps,
        )
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = GestureRecognizer()
        self.activation_manager = ActivationManager(hold_duration=CONFIG.activation.hold_duration)
        self.mouse_controller = MouseController(
            sensitivity=CONFIG.mouse.sensitivity,
            smoothing=CONFIG.mouse.smoothing,
            dead_zone=CONFIG.mouse.dead_zone,
            max_jump=CONFIG.mouse.max_jump,
        )
        self.volume_controller = VolumeController(step=CONFIG.gesture.volume_step)
        self.presentation_controller = PresentationController(
            next_key=CONFIG.presentation.next_key,
            previous_key=CONFIG.presentation.previous_key,
            cooldown=CONFIG.presentation.cooldown,
        )
        self.last_gesture = "NONE"
        self._last_action_times = {}
        self._last_frame_time = time.monotonic()

    def _draw_overlay(self, frame, gesture_name: str, confidence: float, status: str, camera_status: str, landmarks=None) -> None:
        if landmarks:
            connections = (
                ("WRIST", "THUMB_CMC"), ("THUMB_CMC", "THUMB_MCP"), ("THUMB_MCP", "THUMB_IP"), ("THUMB_IP", "THUMB_TIP"),
                ("WRIST", "INDEX_MCP"), ("INDEX_MCP", "INDEX_PIP"), ("INDEX_PIP", "INDEX_DIP"), ("INDEX_DIP", "INDEX_TIP"),
                ("INDEX_MCP", "MIDDLE_MCP"), ("MIDDLE_MCP", "MIDDLE_PIP"), ("MIDDLE_PIP", "MIDDLE_DIP"), ("MIDDLE_DIP", "MIDDLE_TIP"),
                ("MIDDLE_MCP", "RING_MCP"), ("RING_MCP", "RING_PIP"), ("RING_PIP", "RING_DIP"), ("RING_DIP", "RING_TIP"),
                ("RING_MCP", "PINKY_MCP"), ("PINKY_MCP", "PINKY_PIP"), ("PINKY_PIP", "PINKY_DIP"), ("PINKY_DIP", "PINKY_TIP"),
                ("PINKY_MCP", "WRIST"),
            )
            height, width = frame.shape[:2]
            for start, end in connections:
                if start in landmarks and end in landmarks:
                    start_px = (int(landmarks[start][0] * width), int(landmarks[start][1] * height))
                    end_px = (int(landmarks[end][0] * width), int(landmarks[end][1] * height))
                    cv2.line(frame, start_px, end_px, (210, 190, 120), 2)
            for x, y in landmarks.values():
                cv2.circle(frame, (int(x * width), int(y * height)), 3, (255, 255, 255), -1)

        cv2.putText(
            frame,
            f"Gesture: {gesture_name}  Confidence: {confidence:.2f}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Activation: {status}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        count = len(landmarks) if landmarks else 0
        cv2.putText(frame, f"Camera: {camera_status}  Landmarks: {count}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        if landmarks:
            wrist = landmarks.get("WRIST", (0.0, 0.0))
            index_tip = landmarks.get("INDEX_TIP", (0.0, 0.0))
            thumb_tip = landmarks.get("THUMB_TIP", (0.0, 0.0))
            readings = f"Wrist {wrist[0]:.2f},{wrist[1]:.2f}  Index {index_tip[0]:.2f},{index_tip[1]:.2f}  Thumb {thumb_tip[0]:.2f},{thumb_tip[1]:.2f}"
            cv2.putText(frame, readings, (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)

    def _dispatch(self, gesture: str, landmarks, now: float) -> None:
        if gesture == "ONE_FINGER":
            self.mouse_controller.move_from_landmark(landmarks)

        actions = {
            "THUMBS_UP": self.volume_controller.increase,
            "THUMBS_DOWN": self.volume_controller.decrease,
            "TWO_FINGERS": self.presentation_controller.next_slide,
            "ONE_FINGER": self.presentation_controller.previous_slide,
            "PINCH": self.mouse_controller.click,
        }
        action = actions.get(gesture)
        if action is None:
            return
        previous = self._last_action_times.get(gesture, 0.0)
        if now - previous >= CONFIG.gesture.cooldown:
            action()
            self._last_action_times[gesture] = now

    def run(self) -> None:
        if not self.camera.open():
            logger.error("Unable to open webcam. Please check camera permissions and availability.")
            return

        logger.info("Hand Gesture Control desktop app started. Hold open palm to activate.")
        while True:
            now = time.monotonic()
            elapsed = now - self._last_frame_time
            self._last_frame_time = now
            frame = self.camera.read()
            if frame is None:
                logger.error("Failed to read a frame from the camera.")
                self.activation_manager.update("NO_HAND", elapsed)
                break

            result = self.hand_tracker.process_frame(frame)
            if result["status"] != "ok":
                status = self.activation_manager.update("NO_HAND", elapsed)
                self.last_gesture = "NONE"
                self._draw_overlay(frame, "NONE", 0.0, status, result["status"])
                cv2.imshow("Hand Gesture Control", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                continue

            gesture = self.gesture_recognizer.recognize(result["landmarks"])
            if gesture["confidence"] < CONFIG.gesture.confidence_threshold:
                gesture = {"gesture": "NONE", "confidence": gesture["confidence"], "active": False}
            status = self.activation_manager.update(gesture["gesture"], elapsed)
            self.last_gesture = gesture["gesture"]

            if status == "ACTIVE":
                self._dispatch(gesture["gesture"], result["landmarks"], now)

            self._draw_overlay(frame, gesture["gesture"], gesture["confidence"], status, "TRACKING", result["landmarks"])
            cv2.imshow("Hand Gesture Control", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

        self.camera.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hand Gesture Control desktop application")
    parser.add_argument("--camera-index", type=int, default=CONFIG.camera.index, help="Camera index to use")
    parser.add_argument("--width", type=int, default=CONFIG.camera.width, help="Camera width")
    parser.add_argument("--height", type=int, default=CONFIG.camera.height, help="Camera height")
    return parser.parse_args()


def main() -> Optional[int]:
    args = parse_args()
    CONFIG.camera.index = args.camera_index
    CONFIG.camera.width = args.width
    CONFIG.camera.height = args.height

    try:
        app = DesktopGestureApp()
        app.run()
    except Exception as exc:  # pragma: no cover - runtime guard for user-friendly output
        logger.exception("Unable to start the desktop application: %s", exc)
        print("Failed to start the desktop application. See logs for details.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
