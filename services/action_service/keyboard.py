import logging
import time

logger = logging.getLogger(__name__)

try:
    import keyboard as kb
    HAS_KB = True
except ImportError:
    HAS_KB = False


SHORTCUTS = {
    "next_tab": ("ctrl", "tab"), "previous_tab": ("ctrl", "shift", "tab"),
    "new_tab": ("ctrl", "t"), "close_tab": ("ctrl", "w"),
    "task_view": ("win", "tab"), "show_desktop": ("win", "d"),
    "next_desktop": ("ctrl", "win", "right"), "prev_desktop": ("ctrl", "win", "left"),
    "volume_up": ("volume", "up"), "volume_down": ("volume", "down"),
    "mute": ("volume", "mute"), "lock": ("win", "l"),
    "screenshot": ("win", "shift", "s"),
    "confirm": ("enter",), "cancel": ("escape",),
}


class KeyboardController:
    def __init__(self):
        self._cd: dict[str, float] = {}
        self._cd_dur = 0.3

    def send(self, action: str) -> bool:
        if not HAS_KB:
            return False
        now = time.time()
        if now < self._cd.get(action, 0.0):
            return False
        keys = SHORTCUTS.get(action)
        if not keys:
            return False
        try:
            if len(keys) == 1:
                kb.press_and_release(keys[0])
            else:
                kb.send("+".join(keys))
            self._cd[action] = now + self._cd_dur
            return True
        except Exception as e:
            logger.error("Hotkey failed: %s", e)
            return False
