import logging
from typing import Optional

from src.core.gesture_state import GestureEvent, EventType
from src.controllers.mouse import MouseController
from src.controllers.keyboard import KeyboardController
from src.controllers.volume import VolumeController
from src.core.context_manager import ContextManager

logger = logging.getLogger(__name__)


class CommandMapper:
    def __init__(
        self,
        mouse: MouseController,
        keyboard: KeyboardController,
        volume: VolumeController,
        context: ContextManager,
        gesture_config: Optional[dict] = None,
    ):
        self.mouse = mouse
        self.keyboard = keyboard
        self.volume = volume
        self.context = context
        self.gesture_config = gesture_config or {}
        self._context_override = self.gesture_config.get("contexts", {})

    def execute(self, event: GestureEvent, cursor_mode: bool = False):
        if event.event == EventType.PRESS:
            self._handle_press(event, cursor_mode)
        elif event.event == EventType.RELEASE:
            self._handle_release(event, cursor_mode)
        elif event.event == EventType.TAP:
            self._handle_tap(event, cursor_mode)

    def _handle_press(self, event: GestureEvent, cursor_mode: bool):
        g = event.gesture
        if g == "pinch":
            self.mouse.left_down()
        elif g == "closed_fist":
            pos = event.position
            self.mouse.move_cursor(pos[0], pos[1], True)
            self.mouse.left_down()

    def _handle_release(self, event: GestureEvent, cursor_mode: bool):
        g = event.gesture
        if g == "pinch":
            self.mouse.left_up()
        elif g == "closed_fist":
            self.mouse.left_up()

    def _handle_tap(self, event: GestureEvent, cursor_mode: bool):
        g = event.gesture
        action = self._resolve_action(g)
        if action is None:
            return
        if action.startswith("volume_"):
            self._handle_volume(action)
        elif action in ("left_click",):
            self.mouse.left_click()
        elif action in ("right_click",):
            self.mouse.right_click()
        elif action in ("double_click",):
            self.mouse.double_click()
        else:
            self.keyboard.send_hotkey(action)

    def _handle_volume(self, action: str):
        if action == "volume_up":
            self.volume.volume_up()
        elif action == "volume_down":
            self.volume.volume_down()
        elif action == "volume_mute":
            self.volume.mute()

    def _resolve_action(self, gesture: str) -> Optional[str]:
        app = self.context.get_active_app()
        context_map = self._context_override.get(app, {})
        if gesture in context_map:
            return context_map[gesture]
        gesture_cfg = self.gesture_config.get("gestures", {})
        entry = gesture_cfg.get(gesture, {})
        return entry.get("action")

    def update_context(self):
        self.context.get_active_app()
