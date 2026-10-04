from __future__ import annotations

import time

try:
    import pyautogui
except Exception:  # pragma: no cover - environment specific
    pyautogui = None


class PresentationController:
    def __init__(self, next_key: str = "right", previous_key: str = "left", cooldown: float = 0.8) -> None:
        self.next_key = next_key
        self.previous_key = previous_key
        self.cooldown = cooldown
        self.last_command_time = 0.0

    def _can_execute(self) -> bool:
        return time.monotonic() - self.last_command_time >= self.cooldown

    def next_slide(self) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is unavailable because no graphical desktop session is available.")
        if not self._can_execute():
            return
        pyautogui.press(self.next_key)
        self.last_command_time = time.monotonic()

    def previous_slide(self) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is unavailable because no graphical desktop session is available.")
        if not self._can_execute():
            return
        pyautogui.press(self.previous_key)
        self.last_command_time = time.monotonic()
