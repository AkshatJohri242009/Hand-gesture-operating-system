"""Tests for feature extraction from raw MediaPipe landmarks."""
import sys; sys.path.insert(0, '.')

import pytest

from services.gesture_service.feature_extractor import FeatureExtractor
from tests.conftest import (
    make_fd, make_open_palm_landmarks, make_closed_fist_landmarks,
    make_point_landmarks, make_pinch_landmarks, make_thumbs_up_landmarks,
)


class TestFeatureExtractor:
    def test_open_palm_has_extended_fingers(self):
        lm = make_open_palm_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        assert len(f.fingers) == 5
        for fng in f.fingers:
            assert fng.name in ("thumb", "index", "middle", "ring", "pinky")
        states = {fng.name: fng.state.name for fng in f.fingers}
        assert states["index"] == "EXTENDED"
        assert states["middle"] == "EXTENDED"
        assert states["ring"] == "EXTENDED"
        assert states["pinky"] == "EXTENDED"

    def test_closed_fist_has_folded_fingers(self):
        lm = make_closed_fist_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        states = {fng.name: fng.state.name for fng in f.fingers}
        for finger in ("index", "middle", "ring", "pinky"):
            assert states[finger] == "FOLDED", f"{finger} should be FOLDED"

    def test_point_has_index_extended_others_folded(self):
        lm = make_point_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        states = {fng.name: fng.state.name for fng in f.fingers}
        assert states["index"] == "EXTENDED"
        assert states["middle"] == "FOLDED"
        assert states["ring"] == "FOLDED"
        assert states["pinky"] == "FOLDED"

    def test_pinch_has_small_thumb_index_dist(self):
        lm = make_pinch_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        assert f.thumb_index_dist < 0.15, \
            f"pinch thumb-index dist should be small (got {f.thumb_index_dist:.3f})"

    def test_thumbs_up_has_thumb_extended(self):
        lm = make_thumbs_up_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        states = {fng.name: fng.state.name for fng in f.fingers}
        assert states["thumb"] == "EXTENDED"
        assert states["index"] == "FOLDED"
        assert states["middle"] == "FOLDED"
        assert states["ring"] == "FOLDED"
        assert states["pinky"] == "FOLDED"

    def test_palm_normal_computed(self):
        lm = make_open_palm_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        nx, ny, nz = f.palm_normal
        # Should be a unit vector
        norm = (nx**2 + ny**2 + nz**2) ** 0.5
        assert abs(norm - 1.0) < 0.01, f"palm normal not unit ({norm:.3f})"

    def test_velocity_zero_with_single_frame(self):
        lm = make_open_palm_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        assert f.velocity == (0.0, 0.0)
        assert f.speed == 0.0
        assert f.direction == "none"

    def test_velocity_computed_with_two_frames(self):
        extractor = FeatureExtractor()
        h1 = make_fd(landmarks=make_open_palm_landmarks(), palm_center=(0.5, 0.5))
        h2 = make_fd(landmarks=make_open_palm_landmarks(), palm_center=(0.6, 0.5))
        extractor.extract(h1)
        f = extractor.extract(h2)
        assert f.velocity == pytest.approx((0.1, 0.0))
        assert f.speed == pytest.approx(0.1)
        assert f.direction == "right"

    def test_depth_from_middle_mcp(self):
        lm = make_open_palm_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        assert f.depth == lm[9].z

    def test_reset_clears_history(self):
        extractor = FeatureExtractor()
        h1 = make_fd(landmarks=make_open_palm_landmarks(), palm_center=(0.5, 0.5))
        h2 = make_fd(landmarks=make_open_palm_landmarks(), palm_center=(0.6, 0.5))
        extractor.extract(h1)
        extractor.reset()
        f = extractor.extract(h2)
        assert f.speed == 0.0  # no history after reset

    def test_index_middle_dist_positive(self):
        lm = make_peace_landmarks()
        hand = make_fd(landmarks=lm)
        extractor = FeatureExtractor()
        f = extractor.extract(hand)
        # peace sign should have index and middle separated
        assert f.index_middle_dist > 0.05, \
            f"peace sign should have index-middle separation (got {f.index_middle_dist:.3f})"


def make_peace_landmarks():
    from tests.conftest import make_landmarks
    return make_landmarks([
        (0.50, 0.80, 0.00),
        (0.48, 0.72, 0.01),
        (0.47, 0.66, 0.02),
        (0.46, 0.60, 0.03),
        (0.45, 0.54, 0.04),
        (0.54, 0.69, 0.00),
        (0.56, 0.58, 0.01),
        (0.58, 0.46, 0.02),
        (0.60, 0.34, 0.03),
        (0.57, 0.68, 0.01),
        (0.59, 0.57, 0.02),
        (0.61, 0.45, 0.03),
        (0.63, 0.33, 0.04),
        (0.61, 0.67, 0.02),
        (0.62, 0.64, 0.03),
        (0.63, 0.62, 0.04),
        (0.64, 0.61, 0.05),
        (0.65, 0.66, 0.03),
        (0.66, 0.63, 0.04),
        (0.67, 0.61, 0.05),
        (0.68, 0.60, 0.06),
    ])
