from shared.types import (
    Landmark, HandData, HandFeatures, FingerData, FingerState
)
import numpy as np
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class FeatureExtractor:
    FINGER_MAP = [
        ("thumb", 2, 3, 4),
        ("index", 5, 6, 7, 8),
        ("middle", 9, 10, 11, 12),
        ("ring", 13, 14, 15, 16),
        ("pinky", 17, 18, 19, 20),
    ]

    def __init__(self, history_size: int = 10):
        self._history: deque[HandData] = deque(maxlen=history_size)
        self._prev_features: Optional[HandFeatures] = None

    def extract(self, hand: HandData) -> HandFeatures:
        self._history.append(hand)
        lm = hand.landmarks
        if len(lm) < 21:
            return HandFeatures(handedness=hand.handedness)

        fingers = self._extract_fingers(lm)
        palm_w = hand.palm_width

        thumb_tip = lm[4]
        index_tip = lm[8]
        middle_tip = lm[12]
        thumb_index = self._dist(thumb_tip, index_tip) / max(palm_w, 1e-6)
        thumb_middle = self._dist(thumb_tip, middle_tip) / max(palm_w, 1e-6)
        index_middle = self._dist(index_tip, middle_tip) / max(palm_w, 1e-6)

        palm_normal = self._compute_palm_normal(lm)
        orientation = self._classify_orientation(palm_normal)
        hand_angle = np.arctan2(lm[9].y - lm[0].y, lm[9].x - lm[0].x)

        velocity = self._compute_velocity()
        speed = np.sqrt(velocity[0]**2 + velocity[1]**2)
        direction = self._classify_direction(velocity) if speed > 0.01 else "none"

        depth = lm[9].z if len(lm) > 9 else 0.0

        features = HandFeatures(
            handedness=hand.handedness,
            fingers=fingers,
            thumb_index_dist=thumb_index,
            thumb_middle_dist=thumb_middle,
            index_middle_dist=index_middle,
            palm_normal=palm_normal,
            palm_orientation=orientation,
            hand_angle_rad=hand_angle,
            velocity=velocity,
            speed=speed,
            direction=direction,
            depth=depth,
            palm_center=hand.palm_center,
            palm_width=palm_w,
        )
        self._prev_features = features
        return features

    def _extract_fingers(self, lm: list[Landmark]) -> list[FingerData]:
        fingers = []
        for name, *ids in self.FINGER_MAP:
            tip = lm[ids[-1]]
            mcp = lm[ids[0]]
            pip = lm[ids[1]] if len(ids) >= 3 else mcp

            curl = self._dist(tip, mcp) / max(self._dist(pip, mcp), 1e-6)
            if curl > 0.8:
                state = FingerState.EXTENDED
            elif curl < 0.5:
                state = FingerState.FOLDED
            else:
                state = FingerState.HALF

            spread = self._compute_spread_angle(lm, ids[0], ids[-1])

            fingers.append(FingerData(
                name=name,
                state=state,
                curl_ratio=curl,
                tip_position=(tip.x, tip.y, tip.z),
                mcp_position=(mcp.x, mcp.y, mcp.z),
                angle_to_palm=spread,
                spread_angle=spread,
            ))
        return fingers

    def _compute_palm_normal(self, lm: list[Landmark]) -> tuple[float, float, float]:
        wrist = np.array([lm[0].x, lm[0].y, lm[0].z])
        index_mcp = np.array([lm[5].x, lm[5].y, lm[5].z])
        pinky_mcp = np.array([lm[17].x, lm[17].y, lm[17].z])
        v1 = index_mcp - wrist
        v2 = pinky_mcp - wrist
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm < 1e-6:
            return (0.0, 0.0, 1.0)
        normal = normal / norm
        return (float(normal[0]), float(normal[1]), float(normal[2]))

    def _classify_orientation(self, normal: tuple[float, float, float]) -> str:
        nx, ny, nz = normal
        if nz > 0.5:
            return "facing_camera"
        elif nz < -0.5:
            return "facing_away"
        elif nx > 0.5:
            return "facing_right"
        elif nx < -0.5:
            return "facing_left"
        return "unknown"

    def _compute_velocity(self) -> tuple[float, float]:
        if len(self._history) < 2:
            return (0.0, 0.0)
        prev = self._history[-2].palm_center
        curr = self._history[-1].palm_center
        return (curr[0] - prev[0], curr[1] - prev[1])

    def _classify_direction(self, velocity: tuple[float, float]) -> str:
        dx, dy = velocity
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def _compute_spread_angle(self, lm: list[Landmark], id1: int, id2: int) -> float:
        if id1 >= len(lm) or id2 >= len(lm):
            return 0.0
        v1 = np.array([lm[id1].x, lm[id1].y])
        v2 = np.array([lm[id2].x, lm[id2].y])
        wrist = np.array([lm[0].x, lm[0].y])
        a = v1 - wrist
        b = v2 - wrist
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm < 1e-6:
            return 0.0
        return float(np.arccos(np.clip(dot / norm, -1.0, 1.0)))

    def reset(self):
        self._history.clear()
        self._prev_features = None

    @staticmethod
    def _dist(a: Landmark, b: Landmark) -> float:
        return np.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
