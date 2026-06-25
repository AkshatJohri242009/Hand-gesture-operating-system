import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional

from src.vision.hand_tracker import HandData, Landmark

logger = logging.getLogger(__name__)


@dataclass
class GestureFrame:
    label: str = "none"
    confidence: float = 0.0
    hand: str = "unknown"
    palm_center: tuple[float, float] = (0.0, 0.0)
    palm_width: float = 0.0
    features: Optional[dict] = None


class GestureRecognizer:
    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        self.pinch_ratio = cfg.get("pinch_ratio", 0.08)
        self.two_finger_pinch_ratio = cfg.get("two_finger_pinch_ratio", 0.08)
        self.curl_extended = cfg.get("finger_curl_extended", 0.8)
        self.curl_curled = cfg.get("finger_curl_curled", 0.5)
        self.thumb_abduction_angle = cfg.get("thumb_abduction_angle", 30)

    def classify(self, hand: HandData) -> GestureFrame:
        lm = hand.landmarks
        if not lm or len(lm) < 21:
            return GestureFrame(hand=hand.handedness)

        features = self._extract_features(lm, hand.palm_width)
        label, confidence = self._classify_static(features)
        return GestureFrame(
            label=label,
            confidence=confidence,
            hand=hand.handedness,
            palm_center=hand.palm_center,
            palm_width=hand.palm_width,
            features=features,
        )

    def _extract_features(self, lm: list[Landmark], palm_width: float) -> dict:
        pw = max(palm_width, 1e-6)
        curls = {}
        extended = 0
        curled = 0
        finger_names = ["index", "middle", "ring", "pinky"]
        tip_ids = [8, 12, 16, 20]
        mcp_ids = [5, 9, 13, 17]
        pip_ids = [6, 10, 14, 18]

        for name, tip, mcp, pip in zip(finger_names, tip_ids, mcp_ids, pip_ids):
            d_tip_mcp = self._dist(lm[tip], lm[mcp])
            d_pip_mcp = self._dist(lm[pip], lm[mcp])
            curl = d_tip_mcp / max(d_pip_mcp, 1e-6)
            curls[name] = curl
            if curl > self.curl_extended:
                extended += 1
            elif curl < self.curl_curled:
                curled += 1

        thumb_tip = lm[4]
        thumb_mcp = lm[2]
        index_mcp = lm[5]
        index_tip = lm[8]
        middle_tip = lm[12]

        thumb_index_dist = self._dist(thumb_tip, index_tip) / pw
        thumb_middle_dist = self._dist(thumb_tip, middle_tip) / pw

        v_thumb = np.array([thumb_tip.x - thumb_mcp.x, thumb_tip.y - thumb_mcp.y])
        v_index = np.array([index_mcp.x - lm[0].x, index_mcp.y - lm[0].y])
        angle = self._angle_between(v_thumb, v_index) if np.linalg.norm(v_index) > 1e-6 else 0
        thumb_abducted = angle > np.radians(self.thumb_abduction_angle)

        thumb_curl = self._dist(thumb_tip, thumb_mcp) / max(self._dist(lm[3], lm[2]), 1e-6)

        return {
            "curls": curls,
            "extended_count": extended,
            "curled_count": curled,
            "thumb_index_dist": thumb_index_dist,
            "thumb_middle_dist": thumb_middle_dist,
            "thumb_abducted": thumb_abducted,
            "thumb_curl": thumb_curl,
            "thumb_abduction_angle_deg": np.degrees(angle),
        }

    def _classify_static(self, f: dict) -> tuple[str, float]:
        if f["thumb_index_dist"] < self.pinch_ratio:
            return ("pinch", 0.9)
        if f["thumb_middle_dist"] < self.two_finger_pinch_ratio:
            return ("two_finger_pinch", 0.85)
        if f["extended_count"] >= 4 and f["thumb_abducted"]:
            return ("open_palm", 0.85)
        if f["curled_count"] >= 4 and f["thumb_curl"] < self.curl_curled:
            return ("closed_fist", 0.8)
        if f["curled_count"] >= 3 and f["thumb_abducted"] and f["thumb_curl"] > self.curl_extended:
            return ("thumbs_up", 0.75)
        return ("none", 0.0)

    def classify_multi(self, hands: list[HandData]) -> list[GestureFrame]:
        return [self.classify(h) for h in hands]

    @staticmethod
    def _dist(a: Landmark, b: Landmark) -> float:
        return np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

    @staticmethod
    def _angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
        dot = np.dot(v1, v2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return np.arccos(np.clip(dot / max(norm, 1e-6), -1.0, 1.0))
