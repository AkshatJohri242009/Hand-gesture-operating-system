from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


@dataclass
class Landmark:
    x: float
    y: float
    z: float
    visibility: float = 1.0


@dataclass
class HandData:
    landmarks: list[Landmark] = field(default_factory=list)
    handedness: str = "unknown"
    palm_center: tuple[float, float] = (0.0, 0.0)
    palm_width: float = 0.0
    timestamp: float = 0.0


@dataclass
class FaceData:
    landmarks: list[Landmark] = field(default_factory=list)
    head_pose: dict = field(default_factory=lambda: {"pitch": 0.0, "yaw": 0.0, "roll": 0.0})
    left_eye: dict = field(default_factory=lambda: {"center": (0,0), "aspect_ratio": 0.0, "open": True})
    right_eye: dict = field(default_factory=lambda: {"center": (0,0), "aspect_ratio": 0.0, "open": True})
    gaze: tuple[float, float] = (0.0, 0.0)


class FingerState(Enum):
    EXTENDED = auto()
    HALF = auto()
    FOLDED = auto()


@dataclass
class FingerData:
    name: str
    state: FingerState = FingerState.HALF
    curl_ratio: float = 0.0
    tip_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    mcp_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    angle_to_palm: float = 0.0
    spread_angle: float = 0.0


@dataclass
class HandFeatures:
    handedness: str = "unknown"
    fingers: list[FingerData] = field(default_factory=list)
    thumb_index_dist: float = 0.0
    thumb_middle_dist: float = 0.0
    index_middle_dist: float = 0.0
    palm_normal: tuple[float, float, float] = (0.0, 0.0, 0.0)
    palm_orientation: str = "unknown"
    hand_angle_rad: float = 0.0
    velocity: tuple[float, float] = (0.0, 0.0)
    speed: float = 0.0
    direction: str = "none"
    depth: float = 0.0
    palm_center: tuple[float, float] = (0.0, 0.0)
    palm_width: float = 0.0


Gestures = [
    "open_palm", "closed_fist", "pinch", "double_pinch",
    "two_finger_pinch", "point", "peace", "three_fingers",
    "ok_sign", "rock_sign", "thumbs_up",
    "swipe_left", "swipe_right", "swipe_up", "swipe_down",
    "rotate_clockwise", "rotate_counterclockwise",
    "push", "pull", "wave", "circle", "draw_square",
]

class GestureCategory(Enum):
    STATIC = auto()
    DYNAMIC = auto()


class ActivityLabel(Enum):
    STUDYING = "studying"
    CODING = "coding"
    RESEARCHING = "researching"
    BROWSING = "browsing"
    GAMING = "gaming"
    ENTERTAINMENT = "entertainment"
    MEETING = "meeting"
    SOCIAL = "social"
    IDLE = "idle"
    UNKNOWN = "unknown"
