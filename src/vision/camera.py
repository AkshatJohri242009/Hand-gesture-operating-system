import cv2
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    device_id: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    flip_horizontal: bool = True


class Camera:
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_open = False

    def start(self) -> bool:
        self._cap = cv2.VideoCapture(self.config.device_id)
        if not self._cap.isOpened():
            logger.error("Failed to open camera %d", self.config.device_id)
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        self._is_open = True
        logger.info(
            "Camera opened (device=%d, %dx%d)",
            self.config.device_id,
            self.config.width,
            self.config.height,
        )
        return True

    def read(self) -> tuple[bool, Optional[cv2.Mat]]:
        if not self._is_open or self._cap is None:
            return False, None
        ret, frame = self._cap.read()
        if not ret:
            return False, None
        if self.config.flip_horizontal:
            frame = cv2.flip(frame, 1)
        return True, frame

    def release(self):
        if self._cap is not None:
            self._cap.release()
        self._is_open = False
        logger.info("Camera released")

    def is_open(self) -> bool:
        return self._is_open

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.release()
