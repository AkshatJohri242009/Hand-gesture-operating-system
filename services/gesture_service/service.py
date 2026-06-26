import logging
import time
from typing import Optional

from shared.events import bus, Event
from shared.types import HandData, HandFeatures
from .feature_extractor import FeatureExtractor
from .classifier import GestureClassifier
from .state_machine import GestureStateMachine
from .dynamics import MotionAnalyzer
from .gesture_definitions import build_gesture_library

logger = logging.getLogger(__name__)


class GestureService:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.classifier = GestureClassifier(self.feature_extractor)
        self.state_machine = GestureStateMachine()
        self.motion = MotionAnalyzer()
        self._cursor_mode = False
        self._setup()

    def _setup(self):
        lib = build_gesture_library()
        for name, gd in lib.items():
            if gd.category == "static":
                self.state_machine.register_gesture(
                    name=name,
                    hold_frames=gd.hold_frames,
                    cooldown_ms=gd.cooldown_ms,
                    tap_on_release=(name in ("two_finger_pinch", "thumbs_up", "point", "peace", "three_fingers")),
                )
        bus.subscribe("vision.hand.landmarks", self._on_hand_landmarks, "gesture-service")

    def _on_hand_landmarks(self, event: Event):
        hands_data = event.payload.get("hands", [])
        now = time.time()
        main_features = None

        for hdata_dict in hands_data:
            hdata = HandData(
                landmarks=[],  # reconstructed below
                handedness=hdata_dict.get("handedness", "unknown"),
                palm_center=tuple(hdata_dict.get("palm_center", [0.0, 0.0])),
                palm_width=hdata_dict.get("palm_width", 0.0),
                timestamp=now,
            )
            for lm in hdata_dict.get("landmarks", []):
                from shared.types import Landmark
                hdata.landmarks.append(Landmark(**lm))

            features = self.feature_extractor.extract(hdata)
            if main_features is None:
                main_features = features

            static_results = self.classifier.classify(features)
            for gesture_name, confidence, gdef in static_results:
                self.state_machine.update(
                    gesture_name=gesture_name,
                    detected=True,
                    confidence=confidence,
                    hand=hdata.handedness,
                    position=hdata.palm_center,
                )

            self.motion.update(hdata, now)

        self._cursor_mode = self.state_machine.is_cursor_mode()

    @property
    def cursor_mode(self) -> bool:
        return self._cursor_mode

    def get_latest_features(self) -> Optional[HandFeatures]:
        if self.feature_extractor._prev_features:
            return self.feature_extractor._prev_features
        return None

    def shutdown(self):
        bus.unsubscribe("gesture-service")
        logger.info("Gesture service stopped")
