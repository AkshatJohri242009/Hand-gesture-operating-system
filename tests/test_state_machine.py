"""Tests for gesture state machine (IDLE→CANDIDATE→ACTIVE→COOLDOWN)."""
import sys; sys.path.insert(0, '.')

import pytest

from services.gesture_service.state_machine import GestureStateMachine, SMState
from shared.events import bus


@pytest.fixture(autouse=True)
def clear_bus():
    bus.clear()
    yield
    bus.clear()


class TestGestureStateMachine:
    @pytest.fixture
    def sm(self):
        m = GestureStateMachine()
        m.register_gesture("open_palm", hold_frames=3, cooldown_ms=500)
        m.register_gesture("closed_fist", hold_frames=3, cooldown_ms=500,
                           tap_on_release=True)
        return m

    # --- State helpers ---
    def _state(self, sm, name):
        return sm._instances[name].state

    def test_initial_state(self, sm):
        assert self._state(sm, "open_palm") == SMState.IDLE
        assert self._state(sm, "closed_fist") == SMState.IDLE

    def test_not_detected_keeps_idle(self, sm):
        sm.update("open_palm", detected=False, confidence=0.0)
        assert self._state(sm, "open_palm") == SMState.IDLE

    def test_single_detection_goes_candidate(self, sm):
        sm.update("open_palm", detected=True, confidence=0.9)
        assert self._state(sm, "open_palm") == SMState.CANDIDATE

    def test_candidate_miss_returns_to_idle(self, sm):
        sm.update("open_palm", detected=True, confidence=0.9)
        sm.update("open_palm", detected=False, confidence=0.0)
        assert self._state(sm, "open_palm") == SMState.IDLE

    def test_consecutive_matches_reaches_active(self, sm):
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        assert self._state(sm, "open_palm") == SMState.ACTIVE

    def test_release_goes_cooldown(self, sm):
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        sm.update("open_palm", detected=False, confidence=0.0)
        assert self._state(sm, "open_palm") == SMState.COOLDOWN

    def test_cooldown_blocks_immediate_reactivation(self, sm):
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        sm.update("open_palm", detected=False, confidence=0.0)
        # Now COOLDOWN — try to reactivate
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        # Should still be in COOLDOWN (not yet expired)
        assert self._state(sm, "open_palm") == SMState.COOLDOWN

    def test_active_publishes_event(self, sm):
        events = []
        bus.subscribe("gesture.event", lambda e: events.append(e.payload),
                      "test-listener")
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        assert len(events) == 1
        assert events[0]["gesture"] == "open_palm"
        assert events[0]["event_type"] == "press"

    def test_release_publishes_event(self, sm):
        events = []
        bus.subscribe("gesture.event", lambda e: events.append(e.payload),
                      "test-listener")
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        sm.update("open_palm", detected=False, confidence=0.0)
        release_events = [e for e in events if e["event_type"] == "release"]
        assert len(release_events) == 1

    def test_tap_on_release(self, sm):
        events = []
        bus.subscribe("gesture.event", lambda e: events.append(e.payload),
                      "test-listener")
        for _ in range(5):
            sm.update("closed_fist", detected=True, confidence=0.9)
        sm.update("closed_fist", detected=False, confidence=0.0)
        tap_events = [e for e in events if e["event_type"] == "tap"]
        assert len(tap_events) == 1

    def test_cursor_mode_true_when_open_palm_active(self, sm):
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        assert sm.is_cursor_mode() is True

    def test_cursor_mode_false_when_not_active(self, sm):
        assert sm.is_cursor_mode() is False

    def test_reset(self, sm):
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        assert self._state(sm, "open_palm") == SMState.ACTIVE
        sm.reset()
        assert self._state(sm, "open_palm") == SMState.IDLE

    def test_multiple_gestures_independent(self, sm):
        # open_palm active
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        assert self._state(sm, "open_palm") == SMState.ACTIVE
        # closed_fist still idle
        assert self._state(sm, "closed_fist") == SMState.IDLE

    def test_unregistered_gesture_noop(self, sm):
        sm.update("nonexistent", detected=True, confidence=0.9)
        assert "nonexistent" not in sm._instances

    def test_hold_event_after_500ms(self, sm):
        events = []
        bus.subscribe("gesture.event", lambda e: events.append(e.payload),
                      "test-listener")
        for _ in range(5):
            sm.update("open_palm", detected=True, confidence=0.9)
        # Bypass time check by setting active_since far in past
        sm._instances["open_palm"].active_since = 0
        sm.update("open_palm", detected=True, confidence=0.9)
        hold_events = [e for e in events if e["event_type"] == "hold"]
        assert len(hold_events) == 1
