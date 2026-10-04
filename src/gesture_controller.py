from __future__ import annotations

from typing import Dict, Any

from config import CONFIG
from src.controllers.mouse_controller import MouseController
from src.controllers.presentation_controller import PresentationController
from src.controllers.volume_controller import VolumeController
from src.safety.activation_manager import ActivationManager
from src.vision.gesture_recognizer import GestureRecognizer


class GestureController:
    def __init__(self) -> None:
        self.recognizer = GestureRecognizer()
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

    def handle_landmarks(self, landmarks: Dict[str, Any]) -> Dict[str, Any]:
        result = self.recognizer.recognize(landmarks)
        state = self.activation_manager.update(result["gesture"], elapsed=0.033)
        if state != "ACTIVE":
            return {"gesture": result["gesture"], "status": state, "active": False}

        if result["gesture"] == "THUMBS_UP":
            self.volume_controller.increase()
        elif result["gesture"] == "THUMBS_DOWN":
            self.volume_controller.decrease()
        elif result["gesture"] == "TWO_FINGERS":
            self.presentation_controller.next_slide()
        elif result["gesture"] == "ONE_FINGER":
            self.presentation_controller.previous_slide()
        elif result["gesture"] == "PINCH":
            self.mouse_controller.click()
        elif result["gesture"] == "INDEX_MOVEMENT":
            self.mouse_controller.move_from_landmark(landmarks)

        return {"gesture": result["gesture"], "status": "ACTIVE", "active": True}
