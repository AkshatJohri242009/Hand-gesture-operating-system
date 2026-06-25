import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger(__name__)


class GestureState(Enum):
    IDLE = auto()
    CANDIDATE = auto()
    ACTIVE = auto()
    COOLDOWN = auto()


class EventType(Enum):
    PRESS = auto()
    HOLD = auto()
    RELEASE = auto()
    TAP = auto()


@dataclass
class GestureEvent:
    gesture: str
    event: EventType
    hand: str = "unknown"
    confidence: float = 0.0
    position: tuple[float, float] = (0.0, 0.0)
    timestamp: float = 0.0


class SingleGestureSM:
    def __init__(
        self,
        gesture_name: str,
        confirm_frames: int = 3,
        cooldown_ms: int = 200,
        hold_ms: int = 500,
        tap_on_release: bool = False,
    ):
        self.gesture_name = gesture_name
        self.confirm_frames = confirm_frames
        self.cooldown_ms = cooldown_ms
        self.hold_ms = hold_ms
        self.tap_on_release = tap_on_release
        self.state = GestureState.IDLE
        self.candidate_count = 0
        self.active_since: float = 0.0
        self.cooldown_until: float = 0.0
        self.hold_fired = False

    def update(self, detected: bool, confidence: float, now: float) -> Optional[GestureEvent]:
        if self.state == GestureState.COOLDOWN:
            if now >= self.cooldown_until:
                self.state = GestureState.IDLE
            else:
                return None

        if self.state == GestureState.IDLE:
            if detected:
                self.candidate_count = 1
                self.state = GestureState.CANDIDATE
            return None

        if self.state == GestureState.CANDIDATE:
            if detected:
                self.candidate_count += 1
                if self.candidate_count >= self.confirm_frames:
                    self.state = GestureState.ACTIVE
                    self.active_since = now
                    self.hold_fired = False
                    return GestureEvent(
                        gesture=self.gesture_name,
                        event=EventType.PRESS,
                        confidence=confidence,
                        timestamp=now,
                    )
            else:
                self.state = GestureState.IDLE
                self.candidate_count = 0
            return None

        if self.state == GestureState.ACTIVE:
            if not detected:
                self.state = GestureState.COOLDOWN
                self.cooldown_until = now + self.cooldown_ms / 1000.0
                self.candidate_count = 0
                if self.tap_on_release:
                    return GestureEvent(
                        gesture=self.gesture_name,
                        event=EventType.TAP,
                        confidence=confidence,
                        timestamp=now,
                    )
                return GestureEvent(
                    gesture=self.gesture_name,
                    event=EventType.RELEASE,
                    confidence=confidence,
                    timestamp=now,
                )
            if not self.hold_fired and (now - self.active_since) > self.hold_ms / 1000.0:
                self.hold_fired = True
                return GestureEvent(
                    gesture=self.gesture_name,
                    event=EventType.HOLD,
                    confidence=confidence,
                    timestamp=now,
                )
            return None

        return None

    def reset(self):
        self.state = GestureState.IDLE
        self.candidate_count = 0
        self.active_since = 0.0
        self.cooldown_until = 0.0
        self.hold_fired = False


class GestureStateMachine:
    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        confirm = cfg.get("confirm_frames", 3)
        cooldown = cfg.get("cooldown_ms", 200)
        hold = cfg.get("hold_trigger_ms", 500)

        self.sms: dict[str, SingleGestureSM] = {}
        self._register_static(confirm, cooldown, hold)
        self._last_frames: dict[str, any] = {}

    def _register_static(self, confirm: int, cooldown: int, hold: int):
        names = {
            "pinch": dict(tap_on_release=False),
            "two_finger_pinch": dict(tap_on_release=True),
            "closed_fist": dict(tap_on_release=False),
            "thumbs_up": dict(tap_on_release=True),
        }
        for name, opts in names.items():
            self.sms[name] = SingleGestureSM(
                gesture_name=name,
                confirm_frames=confirm,
                cooldown_ms=cooldown,
                hold_ms=hold,
                **opts,
            )

    def is_cursor_mode(self) -> bool:
        return self._last_frames.get("open_palm", False)

    def update(
        self, frames: list, now: float
    ) -> list[GestureEvent]:
        events = []
        detected: dict[str, bool] = {name: False for name in self.sms}
        hand_info: dict[str, str] = {}
        confidence_info: dict[str, float] = {}

        self._last_frames = {}
        for f in frames:
            self._last_frames[f.label] = True

        for f in frames:
            label = f.label
            if label in detected:
                detected[label] = True
                hand_info[label] = f.hand
                confidence_info[label] = f.confidence

        for name, sm in self.sms.items():
            event = sm.update(
                detected.get(name, False),
                confidence_info.get(name, 0.0),
                now,
            )
            if event:
                event.hand = hand_info.get(name, "unknown")
                # attach current position from the frame that triggered it
                for f in frames:
                    if f.label == name:
                        event.position = f.palm_center
                        break
                events.append(event)
        return events

    def reset(self):
        for sm in self.sms.values():
            sm.reset()
