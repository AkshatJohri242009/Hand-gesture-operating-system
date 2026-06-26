import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from mediapipe.tasks.python.vision import hand_landmarker as hl
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat
from mediapipe.tasks.python.core.base_options import BaseOptions

from shared.types import Landmark, HandData

logger = logging.getLogger(__name__)


class HandTracker:
    LANDMARK_IDS = {
        "wrist": 0, "thumb_cmc": 1, "thumb_mcp": 2, "thumb_ip": 3, "thumb_tip": 4,
        "index_mcp": 5, "index_pip": 6, "index_dip": 7, "index_tip": 8,
        "middle_mcp": 9, "middle_pip": 10, "middle_dip": 11, "middle_tip": 12,
        "ring_mcp": 13, "ring_pip": 14, "ring_dip": 15, "ring_tip": 16,
        "pinky_mcp": 17, "pinky_pip": 18, "pinky_dip": 19, "pinky_tip": 20,
    }

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20), (5, 9), (9, 13), (13, 17),
    ]

    def __init__(self, model_path: str = "models/hand_landmarker.task"):
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        options = hl.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_file)),
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = hl.HandLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray) -> list[HandData]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image(ImageFormat.SRGB, rgb)
        result = self._landmarker.detect(image)
        hands = []
        if result.hand_landmarks and result.handedness:
            for hand_landmarks, handedness_list in zip(result.hand_landmarks, result.handedness):
                landmarks = [Landmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility or 1.0) for lm in hand_landmarks]
                if not landmarks:
                    continue
                wrist = landmarks[0]
                middle_mcp = landmarks[9]
                palm_w = self._distance(wrist, middle_mcp)
                cx = sum(lm.x for lm in landmarks) / len(landmarks)
                cy = sum(lm.y for lm in landmarks) / len(landmarks)
                label = handedness_list[0].category_name.lower() if handedness_list else "unknown"
                hands.append(HandData(landmarks=landmarks, handedness=label, palm_center=(cx, cy), palm_width=palm_w))
        return hands

    def draw(self, frame: np.ndarray, hands: list[HandData]):
        for hand in hands:
            lm_list = [(lm.x * frame.shape[1], lm.y * frame.shape[0]) for lm in hand.landmarks]
            for i, (x, y) in enumerate(lm_list):
                cv2.circle(frame, (int(x), int(y)), 4, (0, 255, 0), -1)
            for i, j in self.HAND_CONNECTIONS:
                if i < len(lm_list) and j < len(lm_list):
                    p1, p2 = lm_list[i], lm_list[j]
                    cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
            cv2.putText(frame, hand.handedness, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    def close(self):
        self._landmarker.close()

    @staticmethod
    def _distance(a: Landmark, b: Landmark) -> float:
        return np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)
