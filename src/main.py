import cv2
import logging
import time
from typing import Optional

from src.utils.config import Config
from src.vision.camera import Camera, CameraConfig
from src.vision.hand_tracker import HandTracker
from src.vision.gesture_recognizer import GestureRecognizer
from src.core.gesture_state import GestureStateMachine, EventType
from src.core.gesture_dynamics import DynamicGestureDetector
from src.core.command_mapper import CommandMapper
from src.core.context_manager import ContextManager
from src.controllers.mouse import MouseController, MouseConfig
from src.controllers.keyboard import KeyboardController
from src.controllers.volume import VolumeController

logger = logging.getLogger(__name__)


class ApexControl:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = Config(config_path)
        self.running = False
        self.camera: Optional[Camera] = None
        self.tracker: Optional[HandTracker] = None
        self.recognizer: Optional[GestureRecognizer] = None
        self.state_machine: Optional[GestureStateMachine] = None
        self.dynamics: Optional[DynamicGestureDetector] = None
        self.mapper: Optional[CommandMapper] = None
        self.context: Optional[ContextManager] = None
        self.mouse: Optional[MouseController] = None
        self.keyboard: Optional[KeyboardController] = None
        self.volume: Optional[VolumeController] = None
        self.show_debug = True
        self.cursor_mode = False
        self._last_context_check: float = 0.0

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
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False

        self.tracker = HandTracker(model_path="models/hand_landmarker.task")
        self.recognizer = GestureRecognizer(self.config.thresholds())
        self.state_machine = GestureStateMachine(self.config.state_machine())
        self.dynamics = DynamicGestureDetector(self.config.dynamics())

        gest_cfg = self.config.data
        self.context = ContextManager()
        self.mouse = MouseController(
            MouseConfig(
                sensitivity=self.config.get("mouse.sensitivity", 1.0),
                smoothing=self.config.gesture().get("smoothing", 0.3),
                dead_zone=self.config.gesture().get("dead_zone", 0.02),
            )
        )
        self.keyboard = KeyboardController()
        self.volume = VolumeController()
        self.mapper = CommandMapper(
            mouse=self.mouse,
            keyboard=self.keyboard,
            volume=self.volume,
            context=self.context,
            gesture_config=gest_cfg,
        )

        self.show_debug = self.config.get("gesture.show_debug_overlay", True)
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

                now = time.time()
                hands = self.tracker.process(frame)
                gesture_frames = self.recognizer.classify_multi(hands)
                static_events = self.state_machine.update(gesture_frames, now)
                dynamic_events = self.dynamics.update(hands, now)
                self.cursor_mode = self.state_machine.is_cursor_mode()

                all_events = static_events + dynamic_events

                self.mouse.set_cursor_active(self.cursor_mode)

                primary_hand = hands[0] if hands else None
                if primary_hand:
                    self.mouse.move_cursor(
                        primary_hand.palm_center[0],
                        primary_hand.palm_center[1],
                        self.cursor_mode,
                    )

                for ev in all_events:
                    if ev.event in (EventType.PRESS, EventType.TAP):
                        logger.info("> %s %s", ev.gesture, ev.event.name)
                    self.mapper.execute(ev, self.cursor_mode)

                if now - self._last_context_check > 1.0:
                    self.mapper.update_context()
                    self._last_context_check = now

                if self.show_debug:
                    self.tracker.draw(frame, hands)
                    self._draw_info(frame, gesture_frames, all_events)
                    cv2.imshow("Apex Control — Debug", frame)

                if cv2.waitKey(1) & 0xFF == 27:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _draw_info(self, frame, gesture_frames, events):
        app = self.context.get_active_app() if self.context else "?"
        cv2.putText(
            frame, f"App: {app}", (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
        )
        cursor_label = "CURSOR ON" if self.cursor_mode else "cursor off"
        cv2.putText(
            frame, cursor_label, (frame.shape[1] - 130, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (0, 255, 0) if self.cursor_mode else (100, 100, 100), 2,
        )
        y = 60
        for gf in gesture_frames:
            text = f"{gf.hand}: {gf.label} ({gf.confidence:.2f})"
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            y += 25
        for ev in events[-3:]:
            text = f"> {ev.gesture} [{ev.event.name}]"
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y += 25
        hand_count = len(gesture_frames)
        cv2.putText(
            frame, f"Hands: {hand_count}",
            (frame.shape[1] - 130, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
        )

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
