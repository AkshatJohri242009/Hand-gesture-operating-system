import re
import logging
from typing import Optional

from shared.events import bus

logger = logging.getLogger(__name__)


class IntentParser:
    def __init__(self):
        self._load_commands()

    def _load_commands(self):
        import yaml
        from pathlib import Path
        p = Path("config/voice_commands.yaml")
        self.commands = []
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
                self.commands = data.get("commands", [])
        logger.info("Loaded %d voice commands", len(self.commands))

    def parse(self, text: str) -> Optional[dict]:
        if not text:
            return None
        lower = text.lower().strip()
        for cmd in self.commands:
            trigger = cmd.get("trigger", "")
            try:
                if re.search(trigger, lower):
                    action = cmd.get("action")
                    params = dict(cmd.get("params", {}))
                    for k, v in params.items():
                        if isinstance(v, str) and v.startswith("$"):
                            match = re.search(trigger, lower)
                            if match and match.lastindex and int(v[1:]) <= match.lastindex:
                                params[k] = match.group(int(v[1:]))
                    result = {
                        "text": text,
                        "trigger": trigger,
                        "action": action,
                        "params": params,
                    }
                    bus.publish("voice.intent", result, source="voice-service")
                    return result
            except re.error:
                continue
        return None
