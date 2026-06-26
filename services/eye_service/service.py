import cv2
import logging
import time
import numpy as np
from typing import Optional

from shared.events import bus, Event
from .face_tracker import FaceTracker
from .blink_detector import BlinkDetector, BlinkType
from .gaze_estimator import GazeController
from .head_pose import HeadPoseController

logger = logging.getLogger(__name__)


class EyeService:
    def __init__(self):
        self.tracker: Optional[FaceTracker] = None
        self.blink = BlinkDetector()
        self.gaze = GazeController()
        self.head = HeadPoseController()
        self._setup()

    def _setup(self):
        try:
            self.tracker = FaceTracker(model_path="models/face_landmarker.task")
            logger.info("Eye service initialized")
        except Exception as e:
            logger.warning("Eye service init failed: %s", e)
            self.tracker = None

    def process(self, frame: np.ndarray):
        if self.tracker is None:
            return None

        face = self.tracker.process(frame)
        if face is None:
            return None

        now = time.time()
        self.blink.update(face.left_eye["aspect_ratio"], face.right_eye["aspect_ratio"], now)
        self.gaze.update(face.gaze[0], face.gaze[1], now)
        self.head.update(face.head_pose, now)

        return face

    def draw(self, frame: np.ndarray, face_data):
        if self.tracker:
            self.tracker.draw(frame, face_data)

    def shutdown(self):
        if self.tracker:
            self.tracker.close()
        logger.info("Eye service stopped")
