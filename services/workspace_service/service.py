import logging
import subprocess
from typing import Optional

from shared.events import bus, Event

logger = logging.getLogger(__name__)

try:
    import pygetwindow as gw
    HAS_GW = True
except ImportError:
    HAS_GW = False


WORKSPACES = {
    "study": {
        "apps": ["chrome", "onenote", "spotify"],
        "layout": None,
        "description": "Opens browser, notes, and study playlist",
    },
    "work": {
        "apps": ["chrome", "code", "slack", "spotify"],
        "layout": None,
        "description": "Opens browser, VS Code, Slack, and music",
    },
    "focus": {
        "apps": ["code"],
        "layout": None,
        "description": "Closes distracting apps, opens code editor",
    },
    "meeting": {
        "apps": ["teams", "chrome"],
        "layout": None,
        "description": "Opens Teams/Meet and meeting notes",
    },
    "research": {
        "apps": ["chrome", "zotero", "onenote"],
        "layout": None,
        "description": "Opens browser, reference manager, and notes",
    },
    "gaming": {
        "apps": [],
        "layout": None,
        "description": "Enables DND mode, closes background apps",
    },
}


class WorkspaceEngine:
    def __init__(self):
        self._active_mode: Optional[str] = None
        self._setup()

    def _setup(self):
        bus.subscribe("workspace.launch", self._on_launch, "workspace-service")
        bus.subscribe("voice.command", self._on_voice, "workspace-service")

    def _on_launch(self, event: Event):
        mode = event.payload.get("mode", "")
        self._launch(mode)

    def _on_voice(self, event: Event):
        action = event.payload.get("action", "")
        if action == "smart_context":
            mode = event.payload.get("params", {}).get("mode", "")
            self._launch(mode)

    def _launch(self, mode: str):
        ws = WORKSPACES.get(mode)
        if not ws:
            logger.warning("Unknown workspace: %s", mode)
            return
        logger.info("Launching workspace: %s (%s)", mode, ws["description"])
        self._active_mode = mode
        for app in ws["apps"]:
            self._open_app(app)
        bus.publish("workspace.active", {"mode": mode, "apps": ws["apps"]}, source="workspace-service")

    def _open_app(self, app_name: str):
        try:
            if app_name == "chrome":
                subprocess.Popen(["start", "chrome"], shell=True)
            elif app_name == "code":
                subprocess.Popen(["code"], shell=True)
            elif app_name == "spotify":
                subprocess.Popen(["start", "spotify:"], shell=True)
            elif app_name == "onenote":
                subprocess.Popen(["start", "onenote:"], shell=True)
            elif app_name == "slack":
                subprocess.Popen(["start", "slack:"], shell=True)
            elif app_name == "teams":
                subprocess.Popen(["start", "teams:"], shell=True)
            elif app_name == "zotero":
                subprocess.Popen(["start", "zotero:"], shell=True)
            else:
                subprocess.Popen(["start", app_name], shell=True)
            logger.debug("Launched: %s", app_name)
        except Exception as e:
            logger.error("Failed to launch %s: %s", app_name, e)

    def active_mode(self) -> Optional[str]:
        return self._active_mode

    def shutdown(self):
        bus.unsubscribe("workspace-service")
        logger.info("Workspace service stopped")
