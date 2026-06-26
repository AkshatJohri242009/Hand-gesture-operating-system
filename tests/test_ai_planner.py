"""Tests for AI agent planner — intent→plan decomposition."""
import sys; sys.path.insert(0, '.')

from services.ai_service.graph import _match_plan, planner_node, AgentState


class TestAIPlanner:
    def test_volume_up(self):
        plan = _match_plan("volume up", {})
        assert len(plan) == 1
        assert plan[0]["tool"] == "volume_up"

    def test_volume_down(self):
        plan = _match_plan("volume down", {})
        assert plan[0]["tool"] == "volume_down"

    def test_mute(self):
        plan = _match_plan("mute", {})
        assert plan[0]["tool"] == "volume_mute"

    def test_increase_volume(self):
        plan = _match_plan("increase volume", {})
        assert plan[0]["tool"] == "volume_up"

    def test_screenshot(self):
        plan = _match_plan("screenshot", {})
        assert plan[0]["tool"] == "screenshot"

    def test_click(self):
        plan = _match_plan("click", {})
        assert plan[0]["tool"] == "left_click"

    def test_double_click(self):
        plan = _match_plan("double click", {})
        assert plan[0]["tool"] == "double_click"

    def test_open_chrome(self):
        plan = _match_plan("open chrome", {})
        assert plan[0]["tool"] == "launch_app"
        assert plan[0]["args"]["app_name"] == "chrome"

    def test_open_spotify(self):
        plan = _match_plan("open spotify", {})
        assert plan[0]["tool"] == "launch_app"
        assert plan[0]["args"]["app_name"] == "spotify"

    def test_launch_vs_code(self):
        plan = _match_plan("launch code", {})
        assert plan[0]["tool"] == "launch_app"
        assert plan[0]["args"]["app_name"] == "code"

    def test_search(self):
        plan = _match_plan("search python tutorials", {})
        assert plan[0]["tool"] == "open_url"
        assert "google.com/search" in plan[0]["args"]["url"]
        assert "python+tutorials" in plan[0]["args"]["url"]

    def test_volume_set_number(self):
        plan = _match_plan("set volume 70", {})
        assert plan[0]["tool"] == "volume_set"
        assert plan[0]["args"]["percent"] == 70

    def test_type_text(self):
        plan = _match_plan("type hello world", {})
        assert plan[0]["tool"] == "type_text"
        assert plan[0]["args"]["text"] == "hello world"

    def test_lock(self):
        plan = _match_plan("lock", {})
        assert plan[0]["tool"] == "lock_system"

    def test_unknown_falls_back_to_type(self):
        plan = _match_plan("some random text", {})
        assert plan[0]["tool"] == "type_text"
        assert plan[0]["args"]["text"] == "some random text"

    def test_planner_node_sets_state(self):
        state: AgentState = {
            "intent": "volume up",
            "params": {},
            "plan": [],
            "current_step": 0,
            "results": [],
            "error": None,
            "done": False,
        }
        result = planner_node(state)
        assert len(result["plan"]) == 1
        assert result["plan"][0]["tool"] == "volume_up"
        assert result["current_step"] == 0
        assert result["done"] is False
