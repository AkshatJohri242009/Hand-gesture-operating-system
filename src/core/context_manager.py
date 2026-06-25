import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pygetwindow as gw
    HAS_PYWINDOW = True
except ImportError:
    HAS_PYWINDOW = False
    logger.warning("pygetwindow not available; context awareness disabled")


class ContextManager:
    APP_PATTERNS = {
        "chrome": [r"chrome", r"google chrome"],
        "spotify": [r"spotify"],
        "explorer": [r"explorer", r"file explorer", r"this pc"],
        "vscode": [r"visual studio code", r"vscode", r"code -"],
        "discord": [r"discord"],
        "terminal": [r"terminal", r"powershell", r"cmd", r"command prompt"],
        "browser": [r"firefox", r"edge", r"opera", r"brave"],
    }

    def __init__(self, use_regex: bool = True):
        self._use_regex = use_regex
        self._current_app: str = "default"
        self._current_title: str = ""
        self._poll_interval = 1.0

    def get_active_app(self) -> str:
        if not HAS_PYWINDOW:
            return self._current_app
        try:
            window = gw.getActiveWindow()
            if window is None:
                return self._current_app
            title = window.title.lower()
            if title == self._current_title:
                return self._current_app
            self._current_title = title
            self._current_app = self._match_app(title)
            return self._current_app
        except Exception as e:
            logger.debug("Context check failed: %s", e)
            return self._current_app

    def get_window_title(self) -> str:
        if not HAS_PYWINDOW:
            return ""
        try:
            window = gw.getActiveWindow()
            return window.title if window else ""
        except Exception:
            return ""

    def _match_app(self, title: str) -> str:
        if not self._use_regex:
            return "default"
        for app, patterns in self.APP_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, title, re.IGNORECASE):
                    return app
        return "default"
