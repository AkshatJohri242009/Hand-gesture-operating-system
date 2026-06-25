import logging
import yaml
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ApexControl:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        self.modules = {}

    def _load_config(self, path: str) -> dict:
        config_file = Path(path)
        if not config_file.exists():
            logger.warning(f"Config not found at {path}, using defaults")
            return {}
        with open(config_file) as f:
            return yaml.safe_load(f)

    def initialize(self):
        logger.info("Initializing Apex Control...")
        # Module initialization will be added as components are built
        logger.info("Apex Control initialized")

    def start(self):
        self.running = True
        logger.info("Apex Control started")
        try:
            while self.running:
                # Main loop — will be wired to gesture/voice pipelines
                pass
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        logger.info("Apex Control stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApexControl()
    app.initialize()
    app.start()
