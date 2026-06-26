import logging
from typing import Optional

from shared.types import HandFeatures
from .feature_extractor import FeatureExtractor
from .gesture_definitions import build_gesture_library, features_to_dict, GestureDef

logger = logging.getLogger(__name__)


class GestureClassifier:
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.library = build_gesture_library()
        self._prev_fdict: Optional[dict] = None

    def classify(self, hand_features: HandFeatures) -> list[tuple[str, float, GestureDef]]:
        fdict = features_to_dict(hand_features)
        results = []
        for name, gesture_def in self.library.items():
            if gesture_def.category != "static":
                continue
            matches, score = gesture_def.check(fdict, self._prev_fdict)
            if matches and score >= gesture_def.min_confidence:
                results.append((name, score, gesture_def))
        self._prev_fdict = fdict
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def classify_dynamic(self, hand_features: HandFeatures) -> list[tuple[str, float, GestureDef]]:
        fdict = features_to_dict(hand_features)
        results = []
        for name, gesture_def in self.library.items():
            if gesture_def.category != "dynamic":
                continue
            matches, score = gesture_def.check(fdict, self._prev_fdict)
            if matches and score >= gesture_def.min_confidence:
                results.append((name, score, gesture_def))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_definition(self, name: str) -> Optional[GestureDef]:
        return self.library.get(name)

    def reset(self):
        self.feature_extractor.reset()
        self._prev_fdict = None
