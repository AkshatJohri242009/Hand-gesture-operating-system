"""Tests for voice intent parser — YAML command matching and regex capture."""
import sys; sys.path.insert(0, '.')

import pytest

from services.voice_service.intent_parser import IntentParser


@pytest.fixture(scope="module")
def parser():
    return IntentParser()


class TestIntentParser:
    def test_open_spotify(self, parser):
        r = parser.parse("open spotify")
        assert r is not None
        assert r["action"] == "launch_app"
        assert r["params"]["app"] == "spotify"

    def test_open_chrome(self, parser):
        r = parser.parse("open chrome")
        assert r is not None
        assert r["action"] == "launch_app"
        assert r["params"]["app"] == "chrome"

    def test_volume_up(self, parser):
        r = parser.parse("volume up")
        assert r is not None
        assert r["action"] == "volume_up"

    def test_volume_down(self, parser):
        r = parser.parse("volume down")
        assert r is not None
        assert r["action"] == "volume_down"

    def test_mute(self, parser):
        r = parser.parse("mute")
        assert r["action"] == "volume_mute"

    def test_screenshot(self, parser):
        r = parser.parse("screenshot")
        assert r["action"] == "take_screenshot"

    def test_play_music(self, parser):
        r = parser.parse("play music")
        assert r["action"] == "media_play"

    def test_pause_music(self, parser):
        r = parser.parse("pause music")
        assert r["action"] == "media_pause"

    def test_next_song(self, parser):
        r = parser.parse("next song")
        assert r["action"] == "media_next"

    def test_lock_computer(self, parser):
        r = parser.parse("lock computer")
        assert r["action"] == "lock_system"

    def test_workspace_study(self, parser):
        r = parser.parse("study mode")
        assert r["action"] == "smart_context"
        assert r["params"]["mode"] == "study"

    def test_workspace_work(self, parser):
        r = parser.parse("work mode")
        assert r["action"] == "smart_context"
        assert r["params"]["mode"] == "work"

    def test_workspace_focus(self, parser):
        r = parser.parse("focus mode")
        assert r["action"] == "smart_context"
        assert r["params"]["mode"] == "focus"

    def test_volume_set_regex(self, parser):
        r = parser.parse("volume 50%")
        assert r is not None
        assert r["action"] == "volume_set"
        assert r["params"]["level"] == "50"

    def test_volume_set_regex_75(self, parser):
        r = parser.parse("volume 75%")
        assert r is not None
        assert r["action"] == "volume_set"
        assert r["params"]["level"] == "75"

    def test_ai_query_hey_apex(self, parser):
        r = parser.parse("hey apex open chrome")
        assert r is not None
        assert r["action"] == "ai_query"
        assert r["params"]["text"] == "open chrome"

    def test_ai_query_apex_short(self, parser):
        r = parser.parse("apex volume up")
        assert r is not None
        assert r["action"] == "ai_query"
        assert r["params"]["text"] == "volume up"

    def test_no_match_returns_none(self, parser):
        r = parser.parse("some random gibberish that doesn't match")
        assert r is None

    def test_empty_string(self, parser):
        assert parser.parse("") is None
        assert parser.parse(None) is None

    def test_case_insensitive(self, parser):
        r = parser.parse("OPEN SPOTIFY")
        assert r is not None
        assert r["action"] == "launch_app"
