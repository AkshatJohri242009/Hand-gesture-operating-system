from typing import Any
import numpy as np


class GestureDef:
    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        conditions: list[dict],
        min_confidence: float = 0.7,
        cooldown_ms: int = 200,
        hold_frames: int = 3,
        false_positive_prevention: list[str] = None,
    ):
        self.name = name
        self.category = category
        self.description = description
        self.conditions = conditions
        self.min_confidence = min_confidence
        self.cooldown_ms = cooldown_ms
        self.hold_frames = hold_frames
        self.false_positive_prevention = false_positive_prevention or []

    def check(self, features: dict, prev_features: dict = None) -> tuple[bool, float]:
        matches = []
        total_weight = 0.0
        for cond in self.conditions:
            result = self._evaluate_condition(cond, features, prev_features)
            if result is None:
                continue
            weight = cond.get("weight", 1.0)
            total_weight += weight
            if result:
                matches.append(weight)
        if total_weight == 0.0:
            return False, 0.0
        score = sum(matches) / total_weight
        return score >= 0.6, score

    def _evaluate_condition(self, cond: dict, f: dict, pf: dict = None) -> bool:
        kind = cond.get("type", "feature")
        if kind == "feature":
            return self._check_feature(cond, f)
        elif kind == "dynamic":
            return self._check_dynamic(cond, f, pf)
        elif kind == "finger_state":
            return self._check_finger_state(cond, f)
        return False

    @staticmethod
    def _resolve_key(d: dict, key: str):
        parts = key.split(".")
        for p in parts:
            if isinstance(d, dict):
                d = d.get(p)
            else:
                return None
        return d

    def _check_feature(self, cond: dict, f: dict) -> bool:
        key = cond.get("key", "")
        op = cond.get("op", "lt")
        value = cond.get("value", 0.0)
        actual = self._resolve_key(f, key)
        if actual is None:
            return False
        if op == "lt":
            return actual < value
        elif op == "lte":
            return actual <= value
        elif op == "gt":
            return actual > value
        elif op == "gte":
            return actual >= value
        elif op == "eq":
            return actual == value
        elif op == "neq":
            return actual != value
        elif op == "between":
            return cond["min"] <= actual <= cond["max"]
        elif op == "in":
            return actual in value
        return False

    def _check_dynamic(self, cond: dict, f: dict, pf: dict = None) -> bool:
        if pf is None:
            return False
        key = cond.get("key", "")
        op = cond.get("op", "delta_gt")
        value = cond.get("value", 0.0)
        current = self._resolve_key(f, key) or 0.0
        prev = self._resolve_key(pf, key) or 0.0
        delta = abs(current - prev)
        if op == "delta_gt":
            return delta > value
        elif op == "delta_lt":
            return delta < value
        elif op == "direction":
            sign = current - prev
            if value == "positive":
                return sign > 0
            elif value == "negative":
                return sign < 0
        return False

    def _check_finger_state(self, cond: dict, f: dict) -> bool:
        finger = cond.get("finger", "")
        required = cond.get("state", "EXTENDED")
        fingers = f.get("fingers", [])
        for fng in fingers:
            if fng.get("name") == finger:
                return fng.get("state") == required
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "conditions": self.conditions,
            "min_confidence": self.min_confidence,
            "cooldown_ms": self.cooldown_ms,
            "hold_frames": self.hold_frames,
        }


def build_gesture_library() -> dict[str, GestureDef]:
    lib = {}

    lib["open_palm"] = GestureDef(
        name="open_palm",
        category="static",
        description="All five fingers extended and spread",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "EXTENDED", "weight": 1.0},
            {"type": "feature", "key": "fingers.thumb.angle_to_palm", "op": "gt", "value": 0.5, "weight": 0.5},
        ],
        min_confidence=0.8,
        hold_frames=2,
    )

    lib["closed_fist"] = GestureDef(
        name="closed_fist",
        category="static",
        description="All fingers curled into palm",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "thumb", "state": "FOLDED", "weight": 0.7},
        ],
        min_confidence=0.8,
        hold_frames=3,
        false_positive_prevention=["Ensure thumb is not tucked behind other fingers"],
    )

    lib["pinch"] = GestureDef(
        name="pinch",
        category="static",
        description="Thumb tip touches index fingertip",
        conditions=[
            {"type": "feature", "key": "thumb_index_dist", "op": "lt", "value": 0.08, "weight": 2.0},
            {"type": "finger_state", "finger": "index", "state": "HALF", "weight": 0.5},
            {"type": "finger_state", "finger": "thumb", "state": "HALF", "weight": 0.5},
        ],
        min_confidence=0.85,
        hold_frames=3,
    )

    lib["two_finger_pinch"] = GestureDef(
        name="two_finger_pinch",
        category="static",
        description="Thumb touches middle fingertip",
        conditions=[
            {"type": "feature", "key": "thumb_middle_dist", "op": "lt", "value": 0.08, "weight": 2.0},
            {"type": "feature", "key": "index_middle_dist", "op": "gt", "value": 0.02, "weight": 0.3},
        ],
        min_confidence=0.8,
        hold_frames=3,
    )

    lib["point"] = GestureDef(
        name="point",
        category="static",
        description="Index finger extended, others folded",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "EXTENDED", "weight": 3.0},
            {"type": "finger_state", "finger": "middle", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "FOLDED", "weight": 1.0},
        ],
        min_confidence=0.8,
        hold_frames=2,
    )

    lib["peace"] = GestureDef(
        name="peace",
        category="static",
        description="Index and middle extended (V-sign), others folded",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "FOLDED", "weight": 1.0},
            {"type": "feature", "key": "index_middle_dist", "op": "gt", "value": 0.05, "weight": 0.5},
        ],
        min_confidence=0.75,
        hold_frames=3,
    )

    lib["three_fingers"] = GestureDef(
        name="three_fingers",
        category="static",
        description="Index, middle, ring extended; pinky and thumb folded",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "FOLDED", "weight": 0.8},
        ],
        min_confidence=0.75,
        hold_frames=3,
    )

    lib["thumbs_up"] = GestureDef(
        name="thumbs_up",
        category="static",
        description="Thumb extended upward, all other fingers folded",
        conditions=[
            {"type": "finger_state", "finger": "thumb", "state": "EXTENDED", "weight": 3.0},
            {"type": "finger_state", "finger": "index", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "FOLDED", "weight": 1.0},
        ],
        min_confidence=0.75,
        hold_frames=3,
    )

    lib["ok_sign"] = GestureDef(
        name="ok_sign",
        category="static",
        description="Thumb and index form a circle, other fingers extended",
        conditions=[
            {"type": "feature", "key": "thumb_index_dist", "op": "lt", "value": 0.06, "weight": 2.0},
            {"type": "finger_state", "finger": "middle", "state": "EXTENDED", "weight": 0.5},
            {"type": "finger_state", "finger": "ring", "state": "EXTENDED", "weight": 0.5},
            {"type": "finger_state", "finger": "pinky", "state": "EXTENDED", "weight": 0.5},
        ],
        min_confidence=0.7,
        hold_frames=3,
    )

    lib["rock_sign"] = GestureDef(
        name="rock_sign",
        category="static",
        description="Index and pinky extended, middle and ring folded (horns)",
        conditions=[
            {"type": "finger_state", "finger": "index", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "pinky", "state": "EXTENDED", "weight": 1.0},
            {"type": "finger_state", "finger": "middle", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "ring", "state": "FOLDED", "weight": 1.0},
            {"type": "finger_state", "finger": "thumb", "state": "FOLDED", "weight": 0.5},
        ],
        min_confidence=0.7,
        hold_frames=3,
    )

    lib["swipe_left"] = GestureDef(
        name="swipe_left",
        category="dynamic",
        description="Hand moves rapidly to the left",
        conditions=[
            {"type": "dynamic", "key": "palm_center.x", "op": "direction", "value": "negative", "weight": 2.0},
            {"type": "feature", "key": "speed", "op": "gt", "value": 0.03, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["swipe_right"] = GestureDef(
        name="swipe_right",
        category="dynamic",
        description="Hand moves rapidly to the right",
        conditions=[
            {"type": "dynamic", "key": "palm_center.x", "op": "direction", "value": "positive", "weight": 2.0},
            {"type": "feature", "key": "speed", "op": "gt", "value": 0.03, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["swipe_up"] = GestureDef(
        name="swipe_up",
        category="dynamic",
        description="Hand moves rapidly upward",
        conditions=[
            {"type": "dynamic", "key": "palm_center.y", "op": "direction", "value": "negative", "weight": 2.0},
            {"type": "feature", "key": "speed", "op": "gt", "value": 0.03, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["swipe_down"] = GestureDef(
        name="swipe_down",
        category="dynamic",
        description="Hand moves rapidly downward",
        conditions=[
            {"type": "dynamic", "key": "palm_center.y", "op": "direction", "value": "positive", "weight": 2.0},
            {"type": "feature", "key": "speed", "op": "gt", "value": 0.03, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["rotate_clockwise"] = GestureDef(
        name="rotate_clockwise",
        category="dynamic",
        description="Wrist rotates clockwise (hand angle increases)",
        conditions=[
            {"type": "dynamic", "key": "hand_angle_rad", "op": "direction", "value": "positive", "weight": 2.0},
            {"type": "dynamic", "key": "hand_angle_rad", "op": "delta_gt", "value": 0.5, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["rotate_counterclockwise"] = GestureDef(
        name="rotate_counterclockwise",
        category="dynamic",
        description="Wrist rotates counterclockwise (hand angle decreases)",
        conditions=[
            {"type": "dynamic", "key": "hand_angle_rad", "op": "direction", "value": "negative", "weight": 2.0},
            {"type": "dynamic", "key": "hand_angle_rad", "op": "delta_gt", "value": 0.5, "weight": 1.0},
        ],
        min_confidence=0.7,
        hold_frames=1,
        cooldown_ms=300,
    )

    lib["wave"] = GestureDef(
        name="wave",
        category="dynamic",
        description="Hand moves left-right repeatedly",
        conditions=[
            {"type": "dynamic", "key": "palm_center.x", "op": "direction", "value": "positive", "weight": 0.5},
            {"type": "dynamic", "key": "palm_center.x", "op": "direction", "value": "negative", "weight": 0.5},
            {"type": "feature", "key": "speed", "op": "gt", "value": 0.02, "weight": 1.0},
        ],
        min_confidence=0.6,
        hold_frames=1,
        cooldown_ms=500,
    )

    return lib


def features_to_dict(features) -> dict:
    return {
        "thumb_index_dist": features.thumb_index_dist,
        "thumb_middle_dist": features.thumb_middle_dist,
        "index_middle_dist": features.index_middle_dist,
        "palm_orientation": features.palm_orientation,
        "palm_normal": features.palm_normal,
        "hand_angle_rad": features.hand_angle_rad,
        "speed": features.speed,
        "direction": features.direction,
        "depth": features.depth,
        "palm_center": {"x": features.palm_center[0], "y": features.palm_center[1]},
        "palm_width": features.palm_width,
        "fingers": [
            {
                "name": f.name,
                "state": f.state.name,
                "curl_ratio": f.curl_ratio,
                "angle_to_palm": f.angle_to_palm,
                "spread_angle": f.spread_angle,
            }
            for f in features.fingers
        ],
    }
