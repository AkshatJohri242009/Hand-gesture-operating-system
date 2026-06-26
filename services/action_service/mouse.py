import pyautogui
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MouseConfig:
    sensitivity: float = 1.0
    smoothing: float = 0.3
    dead_zone: float = 0.02
    drag_threshold: int = 5


class MouseController:
    def __init__(self, config: Optional[MouseConfig] = None):
        self.config = config or MouseConfig()
        pyautogui.PAUSE = 0.01
        self._sw, self._sh = pyautogui.size()
        self._px, self._py = pyautogui.position()
        self._active = False
        self._dragging = False
        self._drag_started = False

    def move(self, nx: float, ny: float, present: bool):
        if not self._active or not present:
            if self._dragging:
                self._end_drag()
            return
        tx = nx * self._sw * self.config.sensitivity
        ty = ny * self._sh * self.config.sensitivity
        dx, dy = tx - self._px, ty - self._py
        if abs(dx) < self.config.dead_zone * self._sw and abs(dy) < self.config.dead_zone * self._sh:
            return
        sx = self._px + dx * self.config.smoothing
        sy = self._py + dy * self.config.smoothing
        self._px, self._py = sx, sy
        pyautogui.moveTo(int(sx), int(sy))
        if self._dragging and not self._drag_started:
            if abs(sx - self._dsx) > self.config.drag_threshold or abs(sy - self._dsy) > self.config.drag_threshold:
                self._drag_started = True

    def set_active(self, active: bool):
        self._active = active
        if not active:
            self._end_drag()

    def left_click(self):
        pyautogui.click(button="left")

    def left_down(self):
        self._dragging = True
        self._dsx, self._dsy = pyautogui.position()
        self._drag_started = False
        pyautogui.mouseDown(button="left")

    def left_up(self):
        if self._dragging:
            pyautogui.mouseUp(button="left")
            if not self._drag_started:
                pyautogui.click(button="left")
            self._dragging = False
            self._drag_started = False

    def right_click(self):
        pyautogui.click(button="right")

    def double_click(self):
        pyautogui.doubleClick()

    def scroll(self, clicks: int):
        pyautogui.scroll(clicks)

    def _end_drag(self):
        if self._dragging:
            pyautogui.mouseUp(button="left")
            self._dragging = False
