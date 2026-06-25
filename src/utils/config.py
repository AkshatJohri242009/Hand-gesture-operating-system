import yaml
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, path: str = "config/settings.yaml"):
        self.path = Path(path)
        self.data: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            logger.warning("Config not found at %s, using defaults", self.path)
            self.data = {}
            self._loaded = True
            return self.data
        with open(self.path) as f:
            self.data = yaml.safe_load(f) or {}
        self._loaded = True
        return self.data

    def get(self, key: str, default: Any = None) -> Any:
        if not self._loaded:
            self.load()
        keys = key.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def camera(self) -> dict[str, Any]:
        return self.get("camera", {})

    def gesture(self) -> dict[str, Any]:
        return self.get("gesture", {})

    def thresholds(self) -> dict[str, Any]:
        return self.get("thresholds", {})

    def dynamics(self) -> dict[str, Any]:
        return self.get("dynamics", {})

    def state_machine(self) -> dict[str, Any]:
        return self.get("state_machine", {})
