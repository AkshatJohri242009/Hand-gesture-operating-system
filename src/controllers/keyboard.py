import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import keyboard as kb
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    logger.warning("keyboard module not available; hotkeys disabled")


class KeyboardController:
    SHORTCUTS = {
        "next_tab": ("ctrl", "tab"),
        "previous_tab": ("ctrl", "shift", "tab"),
        "new_tab": ("ctrl", "t"),
        "close_tab": ("ctrl", "w"),
        "task_view": ("win", "tab"),
        "show_desktop": ("win", "d"),
        "next_desktop": ("ctrl", "win", "right"),
        "prev_desktop": ("ctrl", "win", "left"),
        "next_song": ("media", "next"),
        "prev_song": ("media", "prev"),
        "play_pause": ("space",),
        "volume_up": ("volume", "up"),
        "volume_down": ("volume", "down"),
        "mute": ("volume", "mute"),
        "lock": ("win", "l"),
        "screenshot": ("win", "shift", "s"),
        "confirm": ("enter",),
        "cancel": ("escape",),
    }

    def __init__(self):
        self._cooldowns: dict[str, float] = {}
        self._cooldown_duration = 0.3

    def send_hotkey(self, action: str) -> bool:
        if not HAS_KEYBOARD:
            logger.warning("Cannot send %s: keyboard module unavailable", action)
            return False
        now = time.time()
        if now < self._cooldowns.get(action, 0.0):
            return False
        keys = self.SHORTCUTS.get(action)
        if not keys:
            logger.warning("Unknown hotkey action: %s", action)
            return False
        try:
            if len(keys) == 1:
                kb.press_and_release(keys[0])
            else:
                kb.send("+".join(keys))
            self._cooldowns[action] = now + self._cooldown_duration
            logger.debug("Hotkey sent: %s (%s)", action, keys)
            return True
        except Exception as e:
            logger.error("Failed to send hotkey %s: %s", action, e)
            return False
