from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Optional, Tuple

from src.utils.geometry import euclidean_distance

GestureResult = Dict[str, Any]


def _point(landmarks: Dict[str, Any], finger: str, joint: str) -> Optional[Tuple[float, float]]:
    group = landmarks.get(finger)
    value = group.get(joint) if isinstance(group, dict) else landmarks.get(f"{finger}_{joint}")
    if value is None and finger == "WRIST":
        value = landmarks.get("WRIST")
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return float(value[0]), float(value[1])
    return None


def _result(gesture: str, confidence: float = 0.0) -> GestureResult:
    return {"gesture": gesture, "confidence": confidence, "active": gesture != "NONE"}


def _finger_extended(landmarks: Dict[str, Any], finger: str) -> bool:
    wrist = _point(landmarks, "WRIST", "TIP")
    tip = _point(landmarks, finger, "TIP")
    pip = _point(landmarks, finger, "PIP")
    if wrist is None or tip is None or pip is None:
        return False
    return euclidean_distance(wrist, tip) > euclidean_distance(wrist, pip) * 1.08


def _thumb_extended(landmarks: Dict[str, Any]) -> bool:
    mcp = _point(landmarks, "THUMB", "MCP")
    ip = _point(landmarks, "THUMB", "IP")
    tip = _point(landmarks, "THUMB", "TIP")
    if mcp is None or ip is None or tip is None:
        return False
    return euclidean_distance(mcp, tip) > euclidean_distance(mcp, ip) * 1.12


def _finger_states(landmarks: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "THUMB": _thumb_extended(landmarks),
        "INDEX": _finger_extended(landmarks, "INDEX"),
        "MIDDLE": _finger_extended(landmarks, "MIDDLE"),
        "RING": _finger_extended(landmarks, "RING"),
        "PINKY": _finger_extended(landmarks, "PINKY"),
    }


def detect_thumbs_up(landmarks: Dict[str, Any]) -> GestureResult:
    thumb_ip = _point(landmarks, "THUMB", "IP")
    thumb_tip = _point(landmarks, "THUMB", "TIP")
    curled = not any(_finger_states(landmarks)[finger] for finger in ("INDEX", "MIDDLE", "RING", "PINKY"))
    if thumb_ip is not None and thumb_tip is not None and _thumb_extended(landmarks) and curled:
        if thumb_tip[1] < thumb_ip[1] - 0.015:
            return _result("THUMBS_UP", 0.9)
    return _result("NONE")


def detect_thumbs_down(landmarks: Dict[str, Any]) -> GestureResult:
    thumb_ip = _point(landmarks, "THUMB", "IP")
    thumb_tip = _point(landmarks, "THUMB", "TIP")
    curled = not any(_finger_states(landmarks)[finger] for finger in ("INDEX", "MIDDLE", "RING", "PINKY"))
    if thumb_ip is not None and thumb_tip is not None and _thumb_extended(landmarks) and curled:
        if thumb_tip[1] > thumb_ip[1] + 0.015:
            return _result("THUMBS_DOWN", 0.9)
    return _result("NONE")


def detect_open_palm(landmarks: Dict[str, Any]) -> GestureResult:
    states = _finger_states(landmarks)
    if sum(states.values()) >= 4:
        return _result("OPEN_PALM", 0.9)
    return _result("NONE")


def detect_one_finger(landmarks: Dict[str, Any]) -> GestureResult:
    states = _finger_states(landmarks)
    if states["INDEX"] and not any(states[finger] for finger in ("MIDDLE", "RING", "PINKY")):
        return _result("ONE_FINGER", 0.85)
    return _result("NONE")


def detect_two_fingers(landmarks: Dict[str, Any]) -> GestureResult:
    states = _finger_states(landmarks)
    if states["INDEX"] and states["MIDDLE"] and not states["RING"] and not states["PINKY"]:
        return _result("TWO_FINGERS", 0.88)
    return _result("NONE")


def detect_pinch(landmarks: Dict[str, Any], threshold: float = 0.06) -> GestureResult:
    thumb_tip = _point(landmarks, "THUMB", "TIP")
    index_tip = _point(landmarks, "INDEX", "TIP")
    wrist = _point(landmarks, "WRIST", "TIP")
    middle_mcp = _point(landmarks, "MIDDLE", "MCP")
    if thumb_tip is None or index_tip is None or wrist is None or middle_mcp is None:
        return _result("NONE")
    palm_scale = euclidean_distance(wrist, middle_mcp)
    if palm_scale > 0 and euclidean_distance(thumb_tip, index_tip) / palm_scale < threshold:
        return _result("PINCH", 0.9)
    return _result("NONE")


class GestureRecognizer:
    """Classify static hand poses and deliberate vertical hand movement."""

    def __init__(self, pinch_threshold: float = 0.22, movement_threshold: float = 0.035) -> None:
        self.pinch_threshold = pinch_threshold
        self.movement_threshold = movement_threshold
        self._palm_history: Deque[Tuple[float, float]] = deque(maxlen=8)

    def _movement_gesture(self, landmarks: Dict[str, Any]) -> GestureResult:
        wrist = _point(landmarks, "WRIST", "TIP")
        middle_mcp = _point(landmarks, "MIDDLE", "MCP")
        if wrist is None or middle_mcp is None:
            self._palm_history.clear()
            return _result("NONE")

        center = ((wrist[0] + middle_mcp[0]) / 2, (wrist[1] + middle_mcp[1]) / 2)
        previous = self._palm_history[0] if len(self._palm_history) == self._palm_history.maxlen else None
        self._palm_history.append(center)
        if previous is None:
            return _result("NONE")

        delta_y = center[1] - previous[1]
        if abs(delta_y) < self.movement_threshold:
            return _result("NONE")
        confidence = min(0.99, 0.65 + abs(delta_y) * 4)
        return _result("HAND_MOVING_DOWN" if delta_y > 0 else "HAND_MOVING_UP", confidence)

    def recognize(self, landmarks: Dict[str, Any]) -> GestureResult:
        if not landmarks:
            self._palm_history.clear()
            return _result("NONE")

        movement = self._movement_gesture(landmarks)
        if movement["active"]:
            return movement

        detectors = (
            lambda: detect_pinch(landmarks, self.pinch_threshold),
            lambda: detect_thumbs_up(landmarks),
            lambda: detect_thumbs_down(landmarks),
            lambda: detect_open_palm(landmarks),
            lambda: detect_two_fingers(landmarks),
            lambda: detect_one_finger(landmarks),
        )
        for detector in detectors:
            result = detector()
            if result["active"]:
                return result
        return _result("NONE")
