import logging
import subprocess
from typing import Optional

from services.action_service.mouse import MouseController, MouseConfig
from services.action_service.keyboard import KeyboardController
from services.action_service.volume import VolumeController

logger = logging.getLogger(__name__)


class AgentTools:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.volume = VolumeController()

    def move_mouse(self, x: float, y: float):
        self.mouse.move(x, y, True)
        return f"Moved mouse to ({x:.2f}, {y:.2f})"

    def left_click(self):
        self.mouse.left_click()
        return "Left clicked"

    def right_click(self):
        self.mouse.right_click()
        return "Right clicked"

    def double_click(self):
        self.mouse.double_click()
        return "Double clicked"

    def type_text(self, text: str):
        import keyboard as kb
        kb.write(text)
        return f"Typed: {text[:50]}..."

    def press_hotkey(self, *keys: str):
        self.keyboard.send(keys)
        return f"Pressed: {'+'.join(keys)}"

    def volume_up(self):
        self.volume.up()
        return "Volume up"

    def volume_down(self):
        self.volume.down()
        return "Volume down"

    def volume_set(self, percent: int):
        self.volume.set(max(0, min(100, percent)) / 100.0)
        return f"Volume set to {percent}%"

    def volume_mute(self):
        self.volume.mute()
        return "Volume toggled mute"

    def launch_app(self, app_name: str):
        subprocess.Popen(["start", app_name], shell=True)
        return f"Launched {app_name}"

    def screenshot(self):
        self.keyboard.send("screenshot")
        return "Screenshot taken"

    def lock_system(self):
        self.keyboard.send("lock")
        return "System locked"

    def open_url(self, url: str):
        subprocess.Popen(["start", url], shell=True)
        return f"Opened {url}"

    def run_command(self, cmd: str):
        subprocess.Popen(cmd, shell=True)
        return f"Ran: {cmd}"
