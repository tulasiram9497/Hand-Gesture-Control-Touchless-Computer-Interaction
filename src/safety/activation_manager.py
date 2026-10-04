from __future__ import annotations


class ActivationManager:
    def __init__(self, hold_duration: float = 1.5, inactive_after_seconds: float = 2.0) -> None:
        self.hold_duration = hold_duration
        self.inactive_after_seconds = inactive_after_seconds
        self.state = "INACTIVE"
        self._activation_elapsed = 0.0
        self._unknown_elapsed = 0.0

    def update(self, gesture: str, elapsed: float = 0.033) -> str:
        elapsed = max(0.0, elapsed)

        if self.state == "ACTIVE":
            if gesture == "NO_HAND":
                self.reset()
                return self.state
            if gesture == "NONE":
                self._unknown_elapsed += elapsed
                if self._unknown_elapsed >= self.inactive_after_seconds:
                    self.reset()
                    return self.state
            else:
                self._unknown_elapsed = 0.0
            return self.state

        if gesture == "OPEN_PALM":
            self._activation_elapsed += elapsed
            if self._activation_elapsed >= self.hold_duration:
                self.state = "ACTIVE"
                self._unknown_elapsed = 0.0
                return "ACTIVE"
            self.state = "ACTIVATING"
            return "ACTIVATING"

        self._activation_elapsed = 0.0
        self.state = "INACTIVE"
        return "INACTIVE"

    def reset(self) -> None:
        self._activation_elapsed = 0.0
        self._unknown_elapsed = 0.0
        self.state = "INACTIVE"

    def is_active(self) -> bool:
        return self.state == "ACTIVE"
