import logging
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Optional

from shared.events import bus
from shared.types import HandData

logger = logging.getLogger(__name__)


@dataclass
class MotionSample:
    palm_x: float
    palm_y: float
    hand_angle: float
    timestamp: float


class MotionAnalyzer:
    def __init__(self, window: int = 8):
        self._window = window
        self._history: deque[MotionSample] = deque(maxlen=window)
        self._frames_seen = 0
        self._swipe_cooldown = 0.0
        self._rotation_cooldown = 0.0
        self._cooldown_duration = 0.3
        self._min_displacement = 0.15
        self._min_velocity = 0.03
        self._angle_threshold = np.radians(40)

    def update(self, hand: HandData, now: float):
        cx, cy = hand.palm_center
        lm = hand.landmarks
        angle = 0.0
        if len(lm) >= 10:
            angle = np.arctan2(lm[9].y - lm[0].y, lm[9].x - lm[0].x)
        self._history.append(MotionSample(cx, cy, angle, now))
        self._frames_seen += 1

        if self._frames_seen < self._window + 3:
            return
        self._check_swipe(now)
        self._check_rotation(now)

    def _check_swipe(self, now: float):
        if now < self._swipe_cooldown:
            return
        first = self._history[0]
        last = self._history[-1]
        dx = last.palm_x - first.palm_x
        dy = last.palm_y - first.palm_y
        disp = np.sqrt(dx**2 + dy**2)
        if disp < self._min_displacement:
            return
        vel = disp / max(len(self._history), 1)
        if vel < self._min_velocity:
            return
        if abs(dx) > abs(dy):
            direction = "swipe_right" if dx > 0 else "swipe_left"
        else:
            direction = "swipe_down" if dy > 0 else "swipe_up"
        self._swipe_cooldown = now + self._cooldown_duration
        bus.publish(
            topic="gesture.event",
            payload={
                "gesture": direction,
                "event_type": "tap",
                "hand": "unknown",
                "confidence": 0.8,
                "position": [last.palm_x, last.palm_y],
            },
            source="gesture-service",
        )
        logger.info("Dynamic gesture: %s", direction)

    def _check_rotation(self, now: float):
        if now < self._rotation_cooldown:
            return
        first = self._history[0]
        last = self._history[-1]
        delta = last.hand_angle - first.hand_angle
        if abs(delta) < self._angle_threshold:
            return
        direction = "rotate_clockwise" if delta > 0 else "rotate_counterclockwise"
        self._rotation_cooldown = now + self._cooldown_duration
        bus.publish(
            topic="gesture.event",
            payload={
                "gesture": direction,
                "event_type": "tap",
                "hand": "unknown",
                "confidence": 0.75,
                "position": [last.palm_x, last.palm_y],
            },
            source="gesture-service",
        )
        logger.info("Dynamic gesture: %s", direction)

    def reset(self):
        self._history.clear()
        self._frames_seen = 0
