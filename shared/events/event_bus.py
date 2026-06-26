import uuid
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Event:
    topic: str
    payload: dict
    source: str = ""
    event_id: str = ""
    timestamp: float = 0.0
    session_id: str = ""
    confidence: float = 1.0

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()


EventHandler = Callable[[Event], None]


@dataclass
class Subscription:
    topic_pattern: str
    handler: EventHandler
    subscriber_id: str = ""
    once: bool = False


class EventBus:
    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers: list[Subscription] = []
        self._async_pool = ThreadPoolExecutor(max_workers=4)

    def publish(self, topic: str, payload: dict, source: str = "", confidence: float = 1.0) -> Event:
        event = Event(
            topic=topic,
            payload=payload,
            source=source,
            confidence=confidence,
        )
        self._dispatch(event)
        return event

    def publish_event(self, event: Event):
        self._dispatch(event)

    def _dispatch(self, event: Event):
        with self._lock:
            subs = list(self._subscribers)
        for sub in subs:
            if self._match_topic(sub.topic_pattern, event.topic):
                try:
                    if sub.once:
                        self.unsubscribe(sub.subscriber_id)
                    sub.handler(event)
                except Exception as e:
                    logger.error("Handler error for %s: %s", event.topic, e)

    def subscribe_all(self, handler: EventHandler, subscriber_id: str = "") -> str:
        return self.subscribe("*", handler, subscriber_id)

    def subscribe(self, topic_pattern: str, handler: EventHandler, subscriber_id: str = "", once: bool = False) -> str:
        sid = subscriber_id or str(uuid.uuid4())
        with self._lock:
            self._subscribers.append(Subscription(
                topic_pattern=topic_pattern,
                handler=handler,
                subscriber_id=sid,
                once=once,
            ))
        return sid

    def unsubscribe(self, subscriber_id: str):
        with self._lock:
            self._subscribers = [s for s in self._subscribers if s.subscriber_id != subscriber_id]

    def clear(self):
        with self._lock:
            self._subscribers.clear()

    @staticmethod
    def _match_topic(pattern: str, topic: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            return topic.startswith(pattern[:-1])
        if pattern.endswith(".**"):
            return topic.startswith(pattern[:-2])
        return pattern == topic

    def shutdown(self):
        self._async_pool.shutdown(wait=False)
        self.clear()


topics = {
    # Vision
    "vision.frame.captured": "Raw camera frame captured",
    "vision.hand.landmarks": "Hand landmarks detected",
    "vision.face.landmarks": "Face mesh + iris detected",
    "vision.eye.gaze": "Gaze estimated from iris position",
    "vision.eye.blink": "Blink detected (single/double/long)",
    "vision.head.pose": "Head pose direction detected",

    # Gesture
    "gesture.static.detected": "Static gesture recognized per frame",
    "gesture.dynamic.detected": "Dynamic gesture (swipe/rotate) detected",
    "gesture.event": "Gesture event (PRESS/HOLD/RELEASE/TAP)",

    # Voice
    "voice.audio.captured": "Raw audio chunk captured",
    "voice.transcription": "Speech transcribed to text",
    "voice.intent": "Intent parsed from transcription",
    "voice.command": "Voice command recognized",

    # Context
    "context.app.changed": "Active application changed",
    "context.activity.inferred": "User activity inferred",

    # Action
    "action.execute": "Action to be executed on the OS",
    "action.executed": "Action has been executed",

    # Workspace
    "workspace.launch": "Launch a workspace mode",
    "workspace.active": "Workspace mode active",
    "ai.intent": "AI agent intent received",
    "ai.task.planned": "AI agent has a plan",
    "ai.task.executed": "AI agent executed a task",

    # AI
    "ai.intent": "AI agent intent received",
    "ai.task.planned": "AI agent has a plan",
    "ai.task.executed": "AI agent executed a task",

    # System
    "system.initialized": "All services initialized",
    "system.error": "System error occurred",
    "system.shutdown": "System shutting down",
}
