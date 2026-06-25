import cv2
import logging
from pathlib import Path
from typing import Optional

from src.utils.config import Config
from src.vision.camera import Camera, CameraConfig
from src.vision.hand_tracker import HandTracker

logger = logging.getLogger(__name__)


class ApexControl:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = Config(config_path)
        self.running = False
        self.camera: Optional[Camera] = None
        self.tracker: Optional[HandTracker] = None

    def initialize(self):
        logger.info("Initializing Apex Control...")
        cfg = self.config.camera()
        self.camera = Camera(
            CameraConfig(
                device_id=cfg.get("device_id", 0),
                width=cfg.get("width", 640),
                height=cfg.get("height", 480),
                fps=cfg.get("fps", 30),
                flip_horizontal=cfg.get("flip_horizontal", True),
            )
        )
        self.tracker = HandTracker(
            model_path="models/hand_landmarker.task",
        )
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False
        logger.info("Apex Control initialized")
        return True

    def start(self):
        if not self.initialize():
            return
        self.running = True
        logger.info("Apex Control started — press ESC to exit")
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    continue
                hands = self.tracker.process(frame)
                self.tracker.draw(frame, hands)
                cv2.putText(
                    frame,
                    f"Hands: {len(hands)}",
                    (frame.shape[1] - 150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                cv2.imshow("Apex Control — Debug", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.tracker:
            self.tracker.close()
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
        logger.info("Apex Control stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApexControl()
    app.start()
