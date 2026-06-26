import json
import logging
from typing import TypedDict, Sequence, Optional, Any

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    intent: str
    params: dict
    plan: list[dict]
    current_step: int
    results: list[str]
    error: Optional[str]
    done: bool


def _match_plan(intent: str, params: dict) -> list[dict]:
    intent_lower = intent.lower()

    patterns = {
        "open ": ("launch_app", lambda p: {"app_name": p.get("app", intent[5:].strip())}),
        "launch ": ("launch_app", lambda p: {"app_name": p.get("app", intent[7:].strip())}),
        "start ": ("launch_app", lambda p: {"app_name": p.get("app", intent[6:].strip())}),
        "search ": ("open_url", lambda p: {"url": f"https://www.google.com/search?q={p.get('query', intent[7:].strip()).replace(' ', '+')}"}),
        "type ": ("type_text", lambda p: {"text": p.get("text", intent[5:])}),
    }

    word_map = {
        "screenshot": [{"tool": "screenshot", "args": {}}],
        "screenshot": [{"tool": "screenshot", "args": {}}],
        "lock": [{"tool": "lock_system", "args": {}}],
        "volume up": [{"tool": "volume_up", "args": {}}],
        "volume down": [{"tool": "volume_down", "args": {}}],
        "mute": [{"tool": "volume_mute", "args": {}}],
        "increase volume": [{"tool": "volume_up", "args": {}}],
        "decrease volume": [{"tool": "volume_down", "args": {}}],
        "click": [{"tool": "left_click", "args": {}}],
        "double click": [{"tool": "double_click", "args": {}}],
        "right click": [{"tool": "right_click", "args": {}}],
    }

    for phrase, steps in word_map.items():
        if phrase in intent_lower:
            return steps

    for prefix, (tool_name, arg_fn) in patterns.items():
        if intent_lower.startswith(prefix):
            args = arg_fn(params)
            return [{"tool": tool_name, "args": args}]

    if "volume" in intent_lower:
        for word in intent_lower.split():
            if word.isdigit():
                return [{"tool": "volume_set", "args": {"percent": int(word)}}]

    if "search" in intent_lower:
        query = params.get("query", intent_lower.replace("search", "").strip())
        return [{"tool": "open_url", "args": {"url": f"https://www.google.com/search?q={query.replace(' ', '+')}"}}]

    return [{"tool": "type_text", "args": {"text": intent}}]


def planner_node(state: AgentState) -> AgentState:
    plan = _match_plan(state["intent"], state["params"])
    state["plan"] = plan
    state["current_step"] = 0
    state["results"] = []
    state["error"] = None
    state["done"] = False
    logger.info("Plan for '%s': %s", state["intent"], plan)
    return state


def executor_node(state: AgentState, tools: Any) -> AgentState:
    while state["current_step"] < len(state["plan"]):
        step = state["plan"][state["current_step"]]
        tool_name = step["tool"]
        args = step["args"]
        tool_fn = getattr(tools, tool_name, None)
        if tool_fn:
            try:
                result = tool_fn(**args)
                state["results"].append(result)
                logger.info("Step %d: %s(%s) → %s", state["current_step"], tool_name, args, result)
            except Exception as e:
                err = f"Tool {tool_name} failed: {e}"
                state["error"] = err
                logger.error(err)
                break
        else:
            err = f"Unknown tool: {tool_name}"
            state["error"] = err
            logger.error(err)
            break
        state["current_step"] += 1
    state["done"] = state["error"] is None
    return state
