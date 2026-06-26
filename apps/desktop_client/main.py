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
from services.ai_service.service import AIService
from services.hud_service.bridge import HUDWebSocketBridge

logger = logging.getLogger("apex.main")


class ApexControl:
    def __init__(self, camera_id: int = 0):
        self.running = False
        self.camera_id = camera_id
        self.camera: Optional[CameraService] = None
        self.hand_tracker: Optional[HandTracker] = None
        self.gesture: Optional[GestureService] = None
        self.actions: Optional[ActionService] = None
        self.context: Optional[ContextService] = None
        self.eye: Optional[EyeService] = None
        self.voice: Optional[VoiceService] = None
        self.workspace: Optional[WorkspaceEngine] = None
        self.ai: Optional[AIService] = None
        self.hud_bridge: Optional[HUDWebSocketBridge] = None
        self.show_debug = True

        # Performance tracking
        self._fps_counter = 0
        self._fps_last = 0.0
        self._fps = 0.0
        self._latency = {}

    def initialize(self):
        logger.info("Initializing Apex Control...")
        config = self._load_config()

        self.hand_tracker = HandTracker(model_path="models/hand_landmarker.task")
        self.camera = CameraService(device_id=self.camera_id, width=640, height=480)
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
        self.ai = AIService()
        self.hud_bridge = HUDWebSocketBridge()
        self.hud_bridge.start()

        bus.publish("system.initialized", {}, source="apex.main")
        logger.info("Apex Control initialized")
        return True

    def start(self):
        if not self.initialize():
            return
        self.running = True
        self._fps_last = time.time()
        logger.info("Apex Control started — press ESC to exit")

        try:
            while self.running:
                t_frame = time.time()
                ret, frame = self.camera._cap.read()
                if not ret or frame is None:
                    continue
                frame = cv2.flip(frame, 1)

                t_hand = time.time()
                hands = self.hand_tracker.process(frame)
                self._latency["hand"] = time.time() - t_hand

                hands_dicts = []
                for h in hands:
                    hands_dicts.append({
                        "landmarks": [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} for lm in h.landmarks],
                        "handedness": h.handedness,
                        "palm_center": [h.palm_center[0], h.palm_center[1]],
                        "palm_width": h.palm_width,
                    })
                bus.publish("vision.hand.landmarks", {"hands": hands_dicts, "frame_number": 0, "timestamp": time.time()}, source="vision-service")

                t_eye = time.time()
                face_data = self.eye.process(frame)
                self._latency["eye"] = time.time() - t_eye

                time.sleep(0.001)
                self.context.poll()

                cursor = self.gesture.cursor_mode
                self.actions.set_cursor_mode(cursor)
                if hands and cursor:
                    self.actions.update_cursor(hands[0].palm_center[0], hands[0].palm_center[1], True)

                # FPS counter
                self._fps_counter += 1
                now = time.time()
                if now - self._fps_last >= 1.0:
                    self._fps = self._fps_counter / (now - self._fps_last)
                    self._fps_counter = 0
                    self._fps_last = now
                self._latency["frame"] = time.time() - t_frame

                if self.show_debug:
                    self.hand_tracker.draw(frame, hands)
                    self.eye.draw(frame, face_data)
                    app = self.context.current_app()
                    h, w = frame.shape[:2]

                    # Status line
                    latency_str = " | ".join(f"{k}={v*1000:.0f}ms" for k, v in self._latency.items())
                    cv2.putText(frame, f"FPS: {self._fps:.0f}  {latency_str}", (10, 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                    cv2.putText(frame, f"App: {app}", (10, h - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    cv2.putText(frame, "CURSOR ON" if cursor else "cursor off",
                                (w - 140, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (0, 255, 0) if cursor else (100, 100, 100), 2)
                    cv2.putText(frame, f"Hands: {len(hands)}", (w - 140, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    for i, h in enumerate(hands):
                        y = 30 + i * 25
                        label = f"{h.handedness}: {len(h.landmarks)} lm"
                        cv2.putText(frame, label, (10, 45 + i * 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    cv2.imshow("Apex Control", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:
                        break
                    elif key == ord("c"):
                        self.switch_camera()

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def switch_camera(self):
        """Hot-switch to next available camera."""
        self.camera.stop()
        import time as _t
        _t.sleep(0.3)
        for dev in range(5):
            test = cv2.VideoCapture(dev)
            if test and test.isOpened():
                test.release()
                self.camera = CameraService(device_id=dev, width=640, height=480)
                if self.camera.start():
                    self.camera_id = dev
                    logger.info("Switched to camera %d", dev)
                    return
        logger.warning("No alternate camera found")

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
        if self.ai:
            self.ai.shutdown()
        if self.hud_bridge:
            self.hud_bridge.stop()
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
    import argparse
    parser = argparse.ArgumentParser(description="Apex Control")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug overlay")
    args = parser.parse_args()
    setup_logging("apex")
    app = ApexControl(camera_id=args.camera)
    app.show_debug = not args.no_debug
    app.start()
