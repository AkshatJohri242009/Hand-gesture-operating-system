import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from shared.events import bus, Event
from shared.events.schemas import GestureEventPayload, GestureEventType

logger = logging.getLogger(__name__)


class SMState(Enum):
    IDLE = auto()
    CANDIDATE = auto()
    ACTIVE = auto()
    COOLDOWN = auto()


@dataclass
class GestureSMInstance:
    gesture_name: str
    state: SMState = SMState.IDLE
    candidate_count: int = 0
    active_since: float = 0.0
    cooldown_until: float = 0.0
    hold_fired: bool = False


class GestureStateMachine:
    def __init__(self):
        self._instances: dict[str, GestureSMInstance] = {}
        self._cooldown_defaults: dict[str, tuple[int, float, float]] = {}

    def register_gesture(self, name: str, hold_frames: int = 3, cooldown_ms: float = 200, tap_on_release: bool = False):
        self._instances[name] = GestureSMInstance(gesture_name=name)
        self._cooldown_defaults[name] = (hold_frames, cooldown_ms / 1000.0, tap_on_release)

    def update(self, gesture_name: str, detected: bool, confidence: float, hand: str = "unknown",
               position: tuple[float, float] = (0.0, 0.0), features: Optional[dict] = None) -> None:
        defaults = self._cooldown_defaults.get(gesture_name)
        if not defaults:
            return
        hold_frames, cooldown_sec, tap_on_release = defaults

        if gesture_name not in self._instances:
            self._instances[gesture_name] = GestureSMInstance(gesture_name=gesture_name)
        sm = self._instances[gesture_name]
        now = time.time()

        if sm.state == SMState.COOLDOWN:
            if now >= sm.cooldown_until:
                sm.state = SMState.IDLE
            else:
                return

        if sm.state == SMState.IDLE:
            if detected:
                sm.candidate_count = 1
                sm.state = SMState.CANDIDATE
            return

        if sm.state == SMState.CANDIDATE:
            if detected:
                sm.candidate_count += 1
                if sm.candidate_count >= hold_frames:
                    sm.state = SMState.ACTIVE
                    sm.active_since = now
                    sm.hold_fired = False
                    self._emit(gesture_name, GestureEventType.PRESS, confidence, hand, position, features)
            else:
                sm.state = SMState.IDLE
                sm.candidate_count = 0
            return

        if sm.state == SMState.ACTIVE:
            if not detected:
                sm.state = SMState.COOLDOWN
                sm.cooldown_until = now + cooldown_sec
                sm.candidate_count = 0
                if tap_on_release:
                    self._emit(gesture_name, GestureEventType.TAP, confidence, hand, position, features)
                else:
                    self._emit(gesture_name, GestureEventType.RELEASE, confidence, hand, position, features)
                return
            if not sm.hold_fired and (now - sm.active_since) > 0.5:
                sm.hold_fired = True
                self._emit(gesture_name, GestureEventType.HOLD, confidence, hand, position, features)

    def _emit(self, gesture: str, event_type: GestureEventType, confidence: float,
              hand: str, position: tuple[float, float], features: Optional[dict]):
        payload = GestureEventPayload(
            gesture=gesture,
            event_type=event_type,
            hand=hand,
            confidence=confidence,
            position=position,
            features=features,
        )
        bus.publish(
            topic="gesture.event",
            payload={
                "gesture": gesture,
                "event_type": event_type.value,
                "hand": hand,
                "confidence": confidence,
                "position": list(position),
            },
            source="gesture-service",
            confidence=confidence,
        )
        logger.info("Gesture event: %s %s (%.2f, %s)", gesture, event_type.value, confidence, hand)

    def is_cursor_mode(self) -> bool:
        sm = self._instances.get("open_palm")
        return sm is not None and sm.state == SMState.ACTIVE

    def reset(self):
        for sm in self._instances.values():
            sm.state = SMState.IDLE
            sm.candidate_count = 0
            sm.active_since = 0.0
            sm.cooldown_until = 0.0
            sm.hold_fired = False
