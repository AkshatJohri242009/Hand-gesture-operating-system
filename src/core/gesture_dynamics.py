import numpy as np
import logging
from collections import deque
from dataclasses import dataclass
from typing import Optional

from src.vision.hand_tracker import HandData
from src.core.gesture_state import GestureEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class FrameSnapshot:
    palm_center: tuple[float, float]
    hand_angle: float
    timestamp: float


class DynamicGestureDetector:
    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        swipe = cfg.get("swipe", {})
        rotation = cfg.get("rotation", {})
        dp = cfg.get("double_pinch", {})

        self.swipe_window = swipe.get("window_frames", 6)
        self.swipe_displacement = swipe.get("min_displacement", 0.1)
        self.swipe_velocity = swipe.get("min_velocity", 0.02)

        self.rotation_window = rotation.get("window_frames", 5)
        self.rotation_threshold = rotation.get("angle_threshold", 30)

        self.double_pinch_interval = dp.get("max_interval", 0.5)

        self._history: deque[FrameSnapshot] = deque(maxlen=max(self.swipe_window, self.rotation_window))
        self._frames_seen = 0
        self._last_pinch_time: float = 0.0
        self._swipe_cooldown_until: float = 0.0
        self._rotation_cooldown_until: float = 0.0
        self._cooldown_duration: float = 0.3

    def update(self, hands: list[HandData], now: float) -> list[GestureEvent]:
        events = []
        if not hands:
            self._history.clear()
            return events

        primary = hands[0]
        cx, cy = primary.palm_center
        angle = self._compute_hand_angle(primary)

        snapshot = FrameSnapshot(palm_center=(cx, cy), hand_angle=angle, timestamp=now)
        self._history.append(snapshot)
        self._frames_seen += 1

        if self._frames_seen >= self.swipe_window + 3:
            swipe_event = self._detect_swipe(now)
            if swipe_event:
                events.append(swipe_event)

        if self._frames_seen >= self.rotation_window + 3:
            rot_event = self._detect_rotation(now)
            if rot_event:
                events.append(rot_event)

        return events

    def check_double_pinch(self, now: float) -> bool:
        interval = now - self._last_pinch_time
        self._last_pinch_time = now
        if 0 < interval < self.double_pinch_interval:
            self._last_pinch_time = 0.0
            return True
        return False

    def _detect_swipe(self, now: float) -> Optional[GestureEvent]:
        if now < self._swipe_cooldown_until:
            return None
        first = self._history[0]
        last = self._history[-1]
        dx = last.palm_center[0] - first.palm_center[0]
        dy = last.palm_center[1] - first.palm_center[1]
        displacement = np.sqrt(dx**2 + dy**2)
        if displacement < self.swipe_displacement:
            return None
        velocity = displacement / max(len(self._history), 1)
        if velocity < self.swipe_velocity:
            return None
        label = self._classify_swipe_dir(dx, dy)
        self._swipe_cooldown_until = now + self._cooldown_duration
        return GestureEvent(
            gesture=label,
            event=EventType.TAP,
            timestamp=now,
        )

    def _detect_rotation(self, now: float) -> Optional[GestureEvent]:
        if now < self._rotation_cooldown_until:
            return None
        first = self._history[0]
        last = self._history[-1]
        delta = last.hand_angle - first.hand_angle
        if abs(delta) < np.radians(self.rotation_threshold):
            return None
        label = "rotate_clockwise" if delta > 0 else "rotate_counterclockwise"
        self._rotation_cooldown_until = now + self._cooldown_duration
        return GestureEvent(
            gesture=label,
            event=EventType.TAP,
            timestamp=now,
        )

    def _classify_swipe_dir(self, dx: float, dy: float) -> str:
        if abs(dx) > abs(dy):
            return "swipe_right" if dx > 0 else "swipe_left"
        else:
            return "swipe_down" if dy > 0 else "swipe_up"

    def reset(self):
        self._history.clear()
        self._swipe_cooldown_until = 0.0
        self._rotation_cooldown_until = 0.0

    @staticmethod
    def _compute_hand_angle(hand: HandData) -> float:
        lm = hand.landmarks
        if len(lm) < 10:
            return 0.0
        dx = lm[9].x - lm[0].x
        dy = lm[9].y - lm[0].y
        return np.arctan2(dy, dx)
