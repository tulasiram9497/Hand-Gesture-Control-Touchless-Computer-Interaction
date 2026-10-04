from __future__ import annotations

import logging
from typing import Dict, Tuple

try:
    import pyautogui
except Exception:  # pragma: no cover - environment specific
    pyautogui = None

from src.utils.geometry import clamp, map_to_screen
from src.utils.smoothing import ExponentialSmoother

logger = logging.getLogger(__name__)


class MouseController:
    def __init__(self, sensitivity: float = 1.2, smoothing: float = 0.35, dead_zone: float = 0.02, max_jump: float = 0.2) -> None:
        self.sensitivity = sensitivity
        self.smoothing = smoothing
        self.dead_zone = dead_zone
        self.max_jump = max_jump
        self._x_smoother = ExponentialSmoother(alpha=smoothing)
        self._y_smoother = ExponentialSmoother(alpha=smoothing)
        self.last_target: Tuple[float, float] | None = None

    def _screen_size(self) -> Tuple[int, int]:
        if pyautogui is None:
            raise RuntimeError("pyautogui is unavailable because no graphical desktop session is available.")
        return pyautogui.size()

    def move_from_landmark(self, landmarks: Dict[str, Tuple[float, float]]) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is unavailable because no graphical desktop session is available.")
        if "INDEX_TIP" not in landmarks:
            return

        index_tip = landmarks["INDEX_TIP"]
        width, height = self._screen_size()
        normalized_x = clamp(index_tip[0], self.dead_zone, 1.0 - self.dead_zone)
        normalized_y = clamp(index_tip[1], self.dead_zone, 1.0 - self.dead_zone)
        normalized_x = clamp(0.5 + (normalized_x - 0.5) * self.sensitivity, 0.0, 1.0)
        normalized_y = clamp(0.5 + (normalized_y - 0.5) * self.sensitivity, 0.0, 1.0)
        target_x, target_y = map_to_screen((normalized_x, normalized_y), width=width - 1, height=height - 1)

        if self.last_target is not None:
            max_x_delta = width * self.max_jump
            max_y_delta = height * self.max_jump
            target_x = clamp(target_x, self.last_target[0] - max_x_delta, self.last_target[0] + max_x_delta)
            target_y = clamp(target_y, self.last_target[1] - max_y_delta, self.last_target[1] + max_y_delta)

        x = self._x_smoother.update(target_x)
        y = self._y_smoother.update(target_y)

        pyautogui.moveTo(x, y, duration=0.0)
        self.last_target = (x, y)

    def click(self) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is unavailable because no graphical desktop session is available.")
        pyautogui.click()
