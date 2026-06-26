import logging
import re
from typing import Optional

from shared.events import bus, Event
from shared.types import HandFeatures
from .mouse import MouseController, MouseConfig
from .keyboard import KeyboardController
from .volume import VolumeController

logger = logging.getLogger(__name__)


class ActionService:
    def __init__(self, gesture_config: Optional[dict] = None):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.volume = VolumeController()
        self.gesture_config = gesture_config or {}
        self._context_overrides = self.gesture_config.get("contexts", {})
        self._current_app = "default"
        self._cursor_mode = False
        self._setup()

    def _setup(self):
        bus.subscribe("gesture.event", self._on_gesture_event, "action-service")
        bus.subscribe("context.app.changed", self._on_context_change, "action-service")

    def _on_context_change(self, event: Event):
        self._current_app = event.payload.get("app", "default")

    def set_cursor_mode(self, active: bool):
        self._cursor_mode = active
        self.mouse.set_active(active)

    def update_cursor(self, nx: float, ny: float, present: bool):
        self.mouse.move(nx, ny, present)

    def _on_gesture_event(self, event: Event):
        payload = event.payload
        gesture = payload.get("gesture", "")
        event_type = payload.get("event_type", "tap")
        confidence = payload.get("confidence", 0.0)
        position = payload.get("position", [0.0, 0.0])

        if event_type == "press" and gesture == "pinch":
            self.mouse.left_down()
        elif event_type == "release" and gesture == "pinch":
            self.mouse.left_up()
        elif event_type == "press" and gesture == "closed_fist":
            self.mouse.left_down()
        elif event_type == "release" and gesture == "closed_fist":
            self.mouse.left_up()
        elif event_type == "tap":
            self._handle_tap(gesture)

    def _handle_tap(self, gesture: str):
        action = self._resolve_action(gesture)
        if action is None:
            return
        if action.startswith("volume_"):
            if action == "volume_up":
                self.volume.up()
            elif action == "volume_down":
                self.volume.down()
            elif action == "volume_mute":
                self.volume.mute()
        elif action == "left_click":
            self.mouse.left_click()
        elif action == "right_click":
            self.mouse.right_click()
        elif action == "double_click":
            self.mouse.double_click()
        else:
            self.keyboard.send(action)

    def _resolve_action(self, gesture: str) -> Optional[str]:
        context_map = self._context_overrides.get(self._current_app, {})
        if gesture in context_map:
            return context_map[gesture]
        gesture_cfg = self.gesture_config.get("gestures", {})
        entry = gesture_cfg.get(gesture, {})
        return entry.get("action")

    def shutdown(self):
        bus.unsubscribe("action-service")
        logger.info("Action service stopped")
