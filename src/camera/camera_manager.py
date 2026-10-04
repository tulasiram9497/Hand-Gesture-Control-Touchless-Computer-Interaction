from __future__ import annotations

import logging
from typing import Optional

import cv2

logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480, fps: int = 30) -> None:
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.capture: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        self.capture = cv2.VideoCapture(self.index)
        if not self.capture.isOpened():
            logger.error("Unable to open camera index %s.", self.index)
            return False
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        return True

    def read(self):
        if self.capture is None:
            return None
        return self.capture.read()[1]

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
