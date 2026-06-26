import cv2
import logging
import time
from pathlib import Path
from typing import Optional

from shared.events import bus, Event
from shared.types import Landmark

logger = logging.getLogger(__name__)


class CameraService:
    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480):
        self.device_id = device_id
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._frame_count = 0

    def start(self) -> bool:
        self._cap = cv2.VideoCapture(self.device_id)
        if not self._cap or not self._cap.isOpened():
            logger.error("Failed to open camera %d", self.device_id)
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, 30)
        self._running = True
        logger.info("Camera opened (device=%d, %dx%d)", self.device_id, self.width, self.height)
        return True

    def capture_loop(self, hand_tracker):
        import numpy as np
        from mediapipe.tasks.python.vision import hand_landmarker as hl
        from mediapipe.tasks.python.vision.core.image import Image, ImageFormat
        from mediapipe.tasks.python.core.base_options import BaseOptions

        while self._running:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                continue
            frame = cv2.flip(frame, 1)
            self._frame_count += 1
            hands = hand_tracker.process(frame)
            hands_dicts = []
            for h in hands:
                hands_dicts.append({
                    "landmarks": [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} for lm in h.landmarks],
                    "handedness": h.handedness,
                    "palm_center": [h.palm_center[0], h.palm_center[1]],
                    "palm_width": h.palm_width,
                })
            bus.publish(
                topic="vision.hand.landmarks",
                payload={
                    "hands": hands_dicts,
                    "frame_number": self._frame_count,
                    "timestamp": time.time(),
                },
                source="vision-service",
            )
        if self._cap:
            self._cap.release()

    def stop(self):
        self._running = False
        logger.info("Camera stopped")
