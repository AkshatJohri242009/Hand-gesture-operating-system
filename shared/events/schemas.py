from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum, auto


class GestureEventType(Enum):
    PRESS = "press"
    HOLD = "hold"
    RELEASE = "release"
    TAP = "tap"


@dataclass
class GestureEventPayload:
    gesture: str
    event_type: GestureEventType
    hand: str = "unknown"
    confidence: float = 0.0
    position: tuple[float, float] = (0.0, 0.0)
    features: Optional[dict] = None


@dataclass
class HandLandmarkPayload:
    hands: list[dict] = field(default_factory=list)
    frame_number: int = 0


@dataclass
class SpeechPayload:
    text: str = ""
    language: str = "en"
    is_final: bool = True
    confidence: float = 0.0


@dataclass
class IntentPayload:
    intent: str = ""
    entities: dict = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class ActionPayload:
    action: str = ""
    params: dict = field(default_factory=dict)
    reversible: bool = True


@dataclass
class WorkspacePayload:
    mode: str = ""
    apps: list[str] = field(default_factory=list)
    layout: Optional[dict] = None


@dataclass
class ContextPayload:
    app: str = "default"
    window_title: str = ""
    activity: str = "unknown"
    recent_events: list[str] = field(default_factory=list)


@dataclass
class AIPayload:
    intent: str = ""
    plan: list[str] = field(default_factory=list)
    result: str = ""
