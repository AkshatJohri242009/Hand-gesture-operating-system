"""Tests for gesture definitions — verify formal conditions match expected poses."""
import sys; sys.path.insert(0, '.')

import pytest

from services.gesture_service.gesture_definitions import (
    build_gesture_library, features_to_dict,
)
from tests.conftest import make_features


# For gesture definition testing we build features_dict manually
# since that's what GestureDef.check() receives.
def _fd(fingers: dict, tid=0.2, tmd=0.2, imd=0.1, speed=0.0, direction="none",
        palm_center=None, hand_angle_rad=0.0):
    f = make_features(fingers, tid, tmd, imd, speed,
                      palm_center or (0.5, 0.5), direction=direction)
    f.hand_angle_rad = hand_angle_rad
    return features_to_dict(f)


OPEN_PALM_FD = _fd({
    "thumb": "EXTENDED", "index": "EXTENDED", "middle": "EXTENDED",
    "ring": "EXTENDED", "pinky": "EXTENDED",
}, tid=0.3, tmd=0.3, imd=0.12)

CLOSED_FIST_FD = _fd({
    "thumb": "FOLDED", "index": "FOLDED", "middle": "FOLDED",
    "ring": "FOLDED", "pinky": "FOLDED",
}, tid=0.02, tmd=0.02, imd=0.01)

POINT_FD = _fd({
    "thumb": "FOLDED", "index": "EXTENDED", "middle": "FOLDED",
    "ring": "FOLDED", "pinky": "FOLDED",
}, tid=0.15, tmd=0.15, imd=0.04)

PEACE_FD = _fd({
    "thumb": "FOLDED", "index": "EXTENDED", "middle": "EXTENDED",
    "ring": "FOLDED", "pinky": "FOLDED",
}, tid=0.15, tmd=0.15, imd=0.08)

THREE_FINGERS_FD = _fd({
    "index": "EXTENDED", "middle": "EXTENDED", "ring": "EXTENDED",
    "pinky": "FOLDED", "thumb": "FOLDED",
}, tid=0.15, tmd=0.15, imd=0.07)

THUMBS_UP_FD = _fd({
    "thumb": "EXTENDED", "index": "FOLDED", "middle": "FOLDED",
    "ring": "FOLDED", "pinky": "FOLDED",
}, tid=0.15, tmd=0.15, imd=0.03)

PINCH_FD = _fd({
    "thumb": "HALF", "index": "HALF",
    "middle": "EXTENDED", "ring": "EXTENDED", "pinky": "EXTENDED",
}, tid=0.05, tmd=0.15, imd=0.04)

TWO_FINGER_PINCH_FD = _fd({
    "thumb": "HALF", "index": "EXTENDED", "middle": "HALF",
    "ring": "EXTENDED", "pinky": "EXTENDED",
}, tid=0.15, tmd=0.05, imd=0.04)

OK_SIGN_FD = _fd({
    "thumb": "HALF", "index": "HALF",
    "middle": "EXTENDED", "ring": "EXTENDED", "pinky": "EXTENDED",
}, tid=0.04, tmd=0.12, imd=0.06)

ROCK_SIGN_FD = _fd({
    "index": "EXTENDED", "pinky": "EXTENDED",
    "middle": "FOLDED", "ring": "FOLDED", "thumb": "FOLDED",
}, tid=0.12, tmd=0.12, imd=0.04)

WRONG_FD = _fd({
    "thumb": "FOLDED", "index": "FOLDED", "middle": "FOLDED",
    "ring": "FOLDED", "pinky": "FOLDED",
}, tid=0.02, tmd=0.02, imd=0.01)

# Data where thumb_index_dist is large — should NOT match pinch or ok_sign
WIDE_FD = _fd({
    "thumb": "EXTENDED", "index": "EXTENDED", "middle": "EXTENDED",
    "ring": "EXTENDED", "pinky": "EXTENDED",
}, tid=0.25, tmd=0.25, imd=0.10, hand_angle_rad=0.0)


@pytest.fixture(scope="module")
def lib():
    return build_gesture_library()


class TestGestureDefinitions:
    def test_open_palm_matches(self, lib):
        ok, score = lib["open_palm"].check(OPEN_PALM_FD)
        assert ok, f"open_palm should match (score={score:.2f})"
        assert score >= 0.6

    def test_open_palm_rejects_wrong(self, lib):
        ok, score = lib["open_palm"].check(WRONG_FD)
        assert not ok, f"open_palm should reject wrong features (score={score:.2f})"

    def test_closed_fist_matches(self, lib):
        ok, score = lib["closed_fist"].check(CLOSED_FIST_FD)
        assert ok, f"closed_fist should match (score={score:.2f})"

    def test_closed_fist_rejects_open_palm(self, lib):
        ok, score = lib["closed_fist"].check(OPEN_PALM_FD)
        assert not ok, "closed_fist should reject open_palm features"

    def test_pinch_matches(self, lib):
        ok, score = lib["pinch"].check(PINCH_FD)
        assert ok, f"pinch should match (score={score:.2f})"

    def test_pinch_rejects_open_palm(self, lib):
        ok, score = lib["pinch"].check(WIDE_FD)
        assert not ok, f"pinch should reject open palm (score={score:.2f})"

    def test_point_matches(self, lib):
        ok, score = lib["point"].check(POINT_FD)
        assert ok, f"point should match (score={score:.2f})"

    def test_point_rejects_fist(self, lib):
        ok, score = lib["point"].check(CLOSED_FIST_FD)
        assert not ok, f"point should reject fist (score={score:.2f})"

    def test_peace_matches(self, lib):
        ok, score = lib["peace"].check(PEACE_FD)
        assert ok, f"peace should match (score={score:.2f})"

    def test_peace_rejects_fist(self, lib):
        ok, score = lib["peace"].check(CLOSED_FIST_FD)
        assert not ok, f"peace should reject fist (score={score:.2f})"

    def test_three_fingers_matches(self, lib):
        ok, score = lib["three_fingers"].check(THREE_FINGERS_FD)
        assert ok, f"three_fingers should match (score={score:.2f})"

    def test_thumbs_up_matches(self, lib):
        ok, score = lib["thumbs_up"].check(THUMBS_UP_FD)
        assert ok, f"thumbs_up should match (score={score:.2f})"

    def test_thumbs_up_rejects_folded_thumb(self, lib):
        """_fd with thumb FOLDED should not match thumbs_up (thumb must be EXTENDED)."""
        bad = _fd({
            "thumb": "FOLDED", "index": "FOLDED", "middle": "FOLDED",
            "ring": "FOLDED", "pinky": "FOLDED",
        })
        ok, score = lib["thumbs_up"].check(bad)
        assert not ok, f"thumbs_up should reject folded thumb (score={score:.2f})"

    def test_ok_sign_matches(self, lib):
        ok, score = lib["ok_sign"].check(OK_SIGN_FD)
        assert ok, f"ok_sign should match (score={score:.2f})"

    def test_rock_sign_matches(self, lib):
        ok, score = lib["rock_sign"].check(ROCK_SIGN_FD)
        assert ok, f"rock_sign should match (score={score:.2f})"

    def test_two_finger_pinch_matches(self, lib):
        ok, score = lib["two_finger_pinch"].check(TWO_FINGER_PINCH_FD)
        assert ok, f"two_finger_pinch should match (score={score:.2f})"

    def test_swipe_left(self, lib):
        prev = _fd({"thumb": "EXTENDED", "index": "EXTENDED", "middle": "EXTENDED",
                     "ring": "EXTENDED", "pinky": "EXTENDED"},
                   palm_center=(0.6, 0.5))
        curr = _fd({"thumb": "EXTENDED", "index": "EXTENDED", "middle": "EXTENDED",
                     "ring": "EXTENDED", "pinky": "EXTENDED"},
                   palm_center=(0.4, 0.5), speed=0.05, direction="left")
        ok, score = lib["swipe_left"].check(curr, prev)
        assert ok, f"swipe_left should match (score={score:.2f})"

    def test_swipe_right(self, lib):
        prev = _fd({}, palm_center=(0.4, 0.5))
        curr = _fd({}, palm_center=(0.6, 0.5), speed=0.05, direction="right")
        ok, score = lib["swipe_right"].check(curr, prev)
        assert ok, f"swipe_right should match (score={score:.2f})"

    def test_dynamic_gesture_no_prev_returns_false(self, lib):
        fd = _fd({}, speed=0.1)
        ok, _ = lib["swipe_left"].check(fd, None)
        assert not ok, "dynamic gesture with no prev features should fail"

    def test_all_gestures_have_unique_names(self, lib):
        names = list(lib.keys())
        assert len(names) == len(set(names)), "Duplicate gesture names"

    def test_all_gestures_have_conditions(self, lib):
        for name, g in lib.items():
            assert len(g.conditions) > 0, f"{name} has no conditions"
