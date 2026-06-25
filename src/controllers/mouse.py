import pyautogui
import logging
import time
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
        self._screen_w, self._screen_h = pyautogui.size()
        self._prev_x, self._prev_y = pyautogui.position()
        self._cursor_active = False
        self._dragging = False
        self._drag_started = False

    def move_cursor(self, norm_x: float, norm_y: float, hand_present: bool):
        if not self._cursor_active or not hand_present:
            if self._dragging:
                self._end_drag()
            return

        target_x = norm_x * self._screen_w * self.config.sensitivity
        target_y = norm_y * self._screen_h * self.config.sensitivity

        dx = target_x - self._prev_x
        dy = target_y - self._prev_y

        if abs(dx) < self.config.dead_zone * self._screen_w and abs(dy) < self.config.dead_zone * self._screen_h:
            return

        smoothed_x = self._prev_x + dx * self.config.smoothing
        smoothed_y = self._prev_y + dy * self.config.smoothing

        self._prev_x, self._prev_y = smoothed_x, smoothed_y
        pyautogui.moveTo(int(smoothed_x), int(smoothed_y))

        if self._dragging and not self._drag_started:
            drag_dx = abs(smoothed_x - self._drag_start_x)
            drag_dy = abs(smoothed_y - self._drag_start_y)
            if drag_dx > self.config.drag_threshold or drag_dy > self.config.drag_threshold:
                self._drag_started = True

    def set_cursor_active(self, active: bool):
        self._cursor_active = active
        if not active:
            self._end_drag()

    def left_click(self):
        pyautogui.click(button="left")
        logger.debug("Left click")

    def left_down(self):
        self._dragging = True
        self._drag_start_x, self._drag_start_y = pyautogui.position()
        self._drag_started = False
        pyautogui.mouseDown(button="left")
        logger.debug("Left down (drag start)")

    def left_up(self):
        if self._dragging:
            if self._drag_started:
                pyautogui.mouseUp(button="left")
                logger.debug("Left up (drag end)")
            else:
                pyautogui.mouseUp(button="left")
                pyautogui.click(button="left")
                logger.debug("Left up → click (no drag)")
            self._dragging = False
            self._drag_started = False

    def right_click(self):
        pyautogui.click(button="right")
        logger.debug("Right click")

    def double_click(self):
        pyautogui.doubleClick()
        logger.debug("Double click")

    def scroll(self, clicks: int):
        pyautogui.scroll(clicks)
        logger.debug("Scroll %d", clicks)

    def _end_drag(self):
        if self._dragging:
            pyautogui.mouseUp(button="left")
            self._dragging = False
            self._drag_started = False
            logger.debug("Drag ended")
