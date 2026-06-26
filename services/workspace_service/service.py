import logging
import subprocess
import time
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
        "layout": "side_by_side",
        "description": "Opens browser, notes, and study playlist",
    },
    "work": {
        "apps": ["chrome", "code", "slack", "spotify"],
        "layout": "grid",
        "description": "Opens browser, VS Code, Slack, and music",
    },
    "focus": {
        "apps": ["code"],
        "layout": "maximize",
        "description": "Maximizes code editor, minimizes distractions",
    },
    "meeting": {
        "apps": ["chrome", "teams"],
        "layout": "side_by_side",
        "description": "Opens Teams/Meet and meeting notes",
    },
    "research": {
        "apps": ["chrome", "zotero", "onenote"],
        "layout": "grid",
        "description": "Opens browser, reference manager, and notes",
    },
    "gaming": {
        "apps": [],
        "layout": None,
        "description": "Enables DND mode, closes background apps",
    },
}


SCREEN_W, SCREEN_H = 1920, 1080


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
        time.sleep(1.5)
        self._arrange_windows(ws["layout"], ws["apps"])
        bus.publish("workspace.active", {"mode": mode, "apps": ws["apps"]}, source="workspace-service")

    def _arrange_windows(self, layout: Optional[str], apps: list[str]):
        if not HAS_GW or not layout or not apps:
            return
        try:
            windows = gw.getWindowsWithTitle("")
            targets = []
            for app_name in apps:
                for w in windows:
                    if w.title and app_name.lower() in w.title.lower():
                        targets.append(w)
                        break
            if not targets:
                return
            n = len(targets)
            if layout == "maximize":
                for w in targets:
                    w.maximize()
            elif layout == "side_by_side":
                w = int(SCREEN_W / max(n, 1))
                for i, t in enumerate(targets):
                    t.resizeTo(w, SCREEN_H)
                    t.moveTo(i * w, 0)
            elif layout == "grid":
                cols = 2
                rows = (n + cols - 1) // cols
                cw, rh = SCREEN_W // cols, SCREEN_H // rows
                for i, t in enumerate(targets):
                    col = i % cols
                    row = i // cols
                    t.resizeTo(cw, rh)
                    t.moveTo(col * cw, row * rh)
            logger.info("Arranged %d windows in %s layout", n, layout)
        except Exception as e:
            logger.warning("Window arrangement failed: %s", e)

    def _open_app(self, app_name: str):
        try:
            cmds = {
                "chrome": ["start", "chrome"],
                "code": ["code"],
                "spotify": ["start", "spotify:"],
                "onenote": ["start", "onenote:"],
                "slack": ["start", "slack:"],
                "teams": ["start", "teams:"],
                "zotero": ["start", "zotero:"],
            }
            cmd = cmds.get(app_name, ["start", app_name])
            subprocess.Popen(cmd, shell=True)
            logger.debug("Launched: %s", app_name)
        except Exception as e:
            logger.error("Failed to launch %s: %s", app_name, e)

    def active_mode(self) -> Optional[str]:
        return self._active_mode

    def shutdown(self):
        bus.unsubscribe("workspace-service")
        logger.info("Workspace service stopped")
