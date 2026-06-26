import time
import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

from shared.events import bus
from shared.events.schemas import GestureEventPayload, GestureEventType

logger = logging.getLogger(__name__)


class BlinkType(Enum):
    SINGLE = "single_blink"
    DOUBLE = "double_blink"
    LONG = "long_blink"


@dataclass
class BlinkEvent:
    blink_type: BlinkType
    timestamp: float
    confidence: float


class BlinkDetector:
    def __init__(self, ear_threshold: float = 0.2, ear_consec_frames: int = 2):
        self._ear_threshold = ear_threshold
        self._ear_consec_frames = ear_consec_frames
        self._closed_frames = 0
        self._blink_start: float = 0.0
        self._last_blink: float = 0.0
        self._double_candidate: bool = False
        self._double_interval = 0.5
        self._long_duration = 0.8

    def update(self, left_ear: float, right_ear: float, now: float) -> Optional[BlinkEvent]:
        avg_ear = (left_ear + right_ear) / 2.0
        is_closed = avg_ear < self._ear_threshold

        if is_closed:
            if self._closed_frames == 0:
                self._blink_start = now
            self._closed_frames += 1
            return None

        if self._closed_frames > 0:
            duration = now - self._blink_start
            self._closed_frames = 0

            if duration < 0.05:
                return None

            interval = now - self._last_blink
            self._last_blink = now

            if duration > self._long_duration:
                self._double_candidate = False
                ev = BlinkEvent(BlinkType.LONG, now, 0.85)
                self._publish(ev)
                return ev
            elif self._double_candidate and interval < self._double_interval:
                self._double_candidate = False
                ev = BlinkEvent(BlinkType.DOUBLE, now, 0.8)
                self._publish(ev)
                return ev
            else:
                self._double_candidate = True
                ev = BlinkEvent(BlinkType.SINGLE, now, 0.9)
                self._publish(ev)
                return ev

        return None

    def _publish(self, ev: BlinkEvent):
        bus.publish(
            topic="vision.eye.blink",
            payload={
                "blink_type": ev.blink_type.value,
                "confidence": ev.confidence,
                "timestamp": ev.timestamp,
            },
            source="eye-service",
        )
        logger.info("Blink: %s (%.2f)", ev.blink_type.value, ev.confidence)

    def reset(self):
        self._closed_frames = 0
        self._blink_start = 0.0
        self._last_blink = 0.0
        self._double_candidate = False
