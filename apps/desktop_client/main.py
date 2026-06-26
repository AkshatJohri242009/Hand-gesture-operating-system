import cv2
import logging
import time
from typing import Optional

from shared.events import bus, Event
from shared.utils import setup_logging

from services.vision_service.hand_tracker import HandTracker
from services.vision_service.service import CameraService
from services.gesture_service.service import GestureService
from services.action_service.service import ActionService
from services.context_service.service import ContextService
from services.eye_service.service import EyeService
from services.voice_service.service import VoiceService
from services.workspace_service.service import WorkspaceEngine

logger = logging.getLogger("apex.main")


class ApexControl:
    def __init__(self):
        self.running = False
        self.camera: Optional[CameraService] = None
        self.hand_tracker: Optional[HandTracker] = None
        self.gesture: Optional[GestureService] = None
        self.actions: Optional[ActionService] = None
        self.context: Optional[ContextService] = None
        self.eye: Optional[EyeService] = None
        self.voice: Optional[VoiceService] = None
        self.workspace: Optional[WorkspaceEngine] = None
        self.show_debug = True

    def initialize(self):
        logger.info("Initializing Apex Control...")
        config = self._load_config()

        self.hand_tracker = HandTracker(model_path="models/hand_landmarker.task")
        self.camera = CameraService(device_id=0, width=640, height=480)
        if not self.camera.start():
            logger.error("Camera failed")
            return False

        self.gesture = GestureService()
        self.actions = ActionService(gesture_config=config or {})
        self.context = ContextService()
        self.eye = EyeService()
        self.voice = VoiceService()
        self.voice.start()
        self.workspace = WorkspaceEngine()

        bus.publish("system.initialized", {}, source="apex.main")
        logger.info("Apex Control initialized")
        return True

    def start(self):
        if not self.initialize():
            return
        self.running = True
        logger.info("Apex Control started — press ESC to exit")

        try:
            while self.running:
                ret, frame = self.camera._cap.read()
                if not ret or frame is None:
                    continue
                frame = cv2.flip(frame, 1)

                hands = self.hand_tracker.process(frame)

                hands_dicts = []
                for h in hands:
                    hands_dicts.append({
                        "landmarks": [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} for lm in h.landmarks],
                        "handedness": h.handedness,
                        "palm_center": [h.palm_center[0], h.palm_center[1]],
                        "palm_width": h.palm_width,
                    })
                bus.publish("vision.hand.landmarks", {"hands": hands_dicts, "frame_number": 0, "timestamp": time.time()}, source="vision-service")

                face_data = self.eye.process(frame)

                time.sleep(0.001)
                self.context.poll()

                cursor = self.gesture.cursor_mode
                self.actions.set_cursor_mode(cursor)
                if hands and cursor:
                    self.actions.update_cursor(hands[0].palm_center[0], hands[0].palm_center[1], True)

                if self.show_debug:
                    self.hand_tracker.draw(frame, hands)
                    self.eye.draw(frame, face_data)
                    app = self.context.current_app()
                    cv2.putText(frame, f"App: {app}", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    cv2.putText(frame, "CURSOR ON" if cursor else "cursor off", (frame.shape[1] - 130, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if cursor else (100, 100, 100), 2)
                    cv2.putText(frame, f"Hands: {len(hands)}", (frame.shape[1] - 130, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    for i, h in enumerate(hands):
                        y = 60 + i * 25
                        label = f"{h.handedness}: {len(h.landmarks)} lm"
                        cv2.putText(frame, label, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.imshow("Apex Control", frame)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        bus.publish("system.shutdown", {}, source="apex.main")
        bus.shutdown()
        if self.hand_tracker:
            self.hand_tracker.close()
        if self.eye:
            self.eye.shutdown()
        if self.voice:
            self.voice.stop()
        if self.workspace:
            self.workspace.shutdown()
        if self.camera:
            self.camera.stop()
        cv2.destroyAllWindows()
        logger.info("Apex Control stopped")

    @staticmethod
    def _load_config() -> dict:
        import yaml
        from pathlib import Path
        p = Path("config/gestures.yaml")
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f) or {}
        return {}


if __name__ == "__main__":
    setup_logging("apex")
    app = ApexControl()
    app.start()
