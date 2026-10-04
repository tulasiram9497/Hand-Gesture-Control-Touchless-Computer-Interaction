from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

try:
    import pulsectl
except ImportError:  # pragma: no cover - optional dependency
    pulsectl = None

logger = logging.getLogger(__name__)


class VolumeController:
    def __init__(self, step: int = 5) -> None:
        self.step = step
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        if os.name == "nt":
            return "windows"
        if pulsectl is not None:
            return "pulse_relay"
        return "amixer"

    def _get_current_level(self) -> int:
        try:
            if self.backend == "pulse_relay":
                with pulsectl.Pulse("hand-gesture-control") as pulse:
                    sink = pulse.sink_list()[0]
                    return int(float(sink.volume.values[0]) * 100)
            output = subprocess.run(
                ["amixer", "get", "Master"],
                capture_output=True,
                text=True,
                check=False,
            )
            if output.returncode != 0:
                return 0
            for line in output.stdout.splitlines():
                if "Front Left:" in line or "Mono:" in line or "Playback" in line:
                    if "[" in line and "]" in line:
                        text = line.split("[")[1].split("]")[0]
                        if "%" in text:
                            return int(text.strip("%"))
            return 0
        except Exception:
            logger.warning("Unable to determine the current volume level.")
            return 0

    def increase(self) -> None:
        level = self._get_current_level()
        self._set_volume(level + self.step)

    def decrease(self) -> None:
        level = self._get_current_level()
        self._set_volume(level - self.step)

    def _set_volume(self, value: int) -> None:
        value = max(0, min(100, value))
        try:
            if self.backend == "windows":
                try:
                    import ctypes

                    ctypes.windll.winmm.mciSendStringW(f"set cdaudio volume to {value}", None, 0, None)
                except Exception:
                    logger.warning("Windows volume control is not available in this environment.")
                return
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{value}%"], check=False)
        except Exception:
            logger.warning("Unable to set the system volume in this environment.")
