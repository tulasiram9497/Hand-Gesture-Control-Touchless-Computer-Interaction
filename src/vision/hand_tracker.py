from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import cv2

try:
    import mediapipe as mp
except ImportError:  # pragma: no cover - dependency is optional at import time
    mp = None

logger = logging.getLogger(__name__)


HAND_LANDMARK_NAMES = {
    0: "WRIST",
    1: "THUMB_CMC",
    2: "THUMB_MCP",
    3: "THUMB_IP",
    4: "THUMB_TIP",
    5: "INDEX_MCP",
    6: "INDEX_PIP",
    7: "INDEX_DIP",
    8: "INDEX_TIP",
    9: "MIDDLE_MCP",
    10: "MIDDLE_PIP",
    11: "MIDDLE_DIP",
    12: "MIDDLE_TIP",
    13: "RING_MCP",
    14: "RING_PIP",
    15: "RING_DIP",
    16: "RING_TIP",
    17: "PINKY_MCP",
    18: "PINKY_PIP",
    19: "PINKY_DIP",
    20: "PINKY_TIP",
}


class HandTracker:
    def __init__(self, max_hands: int = 1, min_detection_confidence: float = 0.7) -> None:
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence
        self.hands = None
        if mp is not None:
            self.hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=min_detection_confidence,
            )

    def _normalize_landmarks(self, landmark_list: List[Any]) -> Dict[str, tuple[float, float]]:
        normalized: Dict[str, tuple[float, float]] = {}
        for index, landmark in enumerate(landmark_list):
            key_name = HAND_LANDMARK_NAMES.get(index, f"LANDMARK_{index}")
            normalized[key_name] = (float(landmark.x), float(landmark.y))
        return normalized

    def process_frame(self, frame) -> Dict[str, Any]:
        if self.hands is None:
            return {"status": "missing_dependency", "landmarks": None}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if not results.multi_hand_landmarks:
            return {"status": "no_hand", "landmarks": None}
        if len(results.multi_hand_landmarks) > 1:
            return {"status": "multiple_hands", "landmarks": None}

        landmarks = results.multi_hand_landmarks[0]
        normalized = self._normalize_landmarks(landmarks.landmark)
        return {"status": "ok", "landmarks": normalized}
