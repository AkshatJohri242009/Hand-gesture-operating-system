import logging
import re
import time
from typing import Optional

from shared.events import bus, Event
from shared.types import ActivityLabel

logger = logging.getLogger(__name__)

try:
    import pygetwindow as gw
    HAS_GW = True
except ImportError:
    HAS_GW = False


APP_PATTERNS = {
    "chrome": [r"chrome", r"google chrome"],
    "spotify": [r"spotify"],
    "explorer": [r"explorer", r"file explorer", r"this pc"],
    "vscode": [r"visual studio code", r"vscode", r"code -"],
    "discord": [r"discord"],
    "terminal": [r"terminal", r"powershell", r"cmd", r"command prompt"],
    "browser": [r"firefox", r"edge", r"opera", r"brave"],
    "teams": [r"teams", r"microsoft teams"],
    "zoom": [r"zoom"],
    "notion": [r"notion"],
}

# Activity inference rules: (app_patterns, activity_label)
ACTIVITY_RULES = [
    (["vscode", "terminal"], ActivityLabel.CODING),
    (["onenote", "notion", "word", "pdf"], ActivityLabel.STUDYING),
    (["zotero", "chrome.*scholar", "chrome.*arxiv"], ActivityLabel.RESEARCHING),
    (["chrome", "browser", "edge", "firefox"], ActivityLabel.BROWSING),
    (["teams", "zoom", "slack"], ActivityLabel.MEETING),
    (["spotify", "netflix", "youtube"], ActivityLabel.ENTERTAINMENT),
    (["discord"], ActivityLabel.SOCIAL),
]


class ContextService:
    def __init__(self):
        self._current_app = "default"
        self._current_title = ""
        self._current_activity = ActivityLabel.UNKNOWN
        self._last_poll = 0.0

    def poll(self):
        now = time.time()
        if now - self._last_poll < 1.0:
            return
        self._last_poll = now
        if not HAS_GW:
            return
        try:
            window = gw.getActiveWindow()
            if window is None:
                return
            title = window.title.lower()
            if title == self._current_title:
                return
            self._current_title = title
            old_app = self._current_app
            self._current_app = self._match(title)
            if old_app != self._current_app:
                bus.publish("context.app.changed", {"app": self._current_app, "title": title}, source="context-service")
            self._infer_activity(self._current_app, title)
        except:
            pass

    def _infer_activity(self, app: str, title: str):
        for patterns, activity in ACTIVITY_RULES:
            for pat in patterns:
                if re.search(pat, app + " " + title, re.IGNORECASE):
                    if self._current_activity != activity:
                        self._current_activity = activity
                        bus.publish("context.activity.inferred", {"activity": activity.value, "app": app, "title": title}, source="context-service")
                        logger.info("Activity: %s (from %s)", activity.value, app)
                    return
        if self._current_activity != ActivityLabel.UNKNOWN:
            self._current_activity = ActivityLabel.UNKNOWN

    def current_app(self) -> str:
        return self._current_app

    def current_title(self) -> str:
        return self._current_title

    def current_activity(self) -> ActivityLabel:
        return self._current_activity

    def _match(self, title: str) -> str:
        for app, patterns in APP_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, title, re.IGNORECASE):
                    return app
        return "default"
