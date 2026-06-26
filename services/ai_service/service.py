import json
import logging
from functools import partial
from typing import Optional

from shared.events import bus, Event
from .tools import AgentTools
from .graph import AgentState, planner_node, executor_node

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


SYSTEM_PROMPT = """You are a computer control agent. Given a user request, output a JSON array of tool calls.
Available tools and their parameters:
- launch_app(app_name: str) - Open an application
- open_url(url: str) - Open a URL in browser
- type_text(text: str) - Type text at cursor
- left_click() - Left mouse click
- right_click() - Right mouse click
- double_click() - Double click
- volume_up() - Increase volume
- volume_down() - Decrease volume
- volume_set(percent: int) - Set volume 0-100
- volume_mute() - Toggle mute
- screenshot() - Take screenshot
- lock_system() - Lock computer
- press_hotkey(*keys: str) - Press key combination

Output ONLY a JSON array of {"tool": "name", "args": {...}}.
Example: [{"tool": "launch_app", "args": {"app_name": "chrome"}}]"""


def _ollama_planner(intent: str) -> Optional[list[dict]]:
    try:
        resp = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": intent},
            ],
            options={"temperature": 0.1, "num_predict": 512},
        )
        text = resp["message"]["content"].strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        plan = json.loads(text)
        if isinstance(plan, list) and all("tool" in p for p in plan):
            return plan
    except Exception as e:
        logger.debug("Ollama planner failed: %s", e)
    return None


class AIService:
    def __init__(self, use_llm: bool = True):
        self.tools = AgentTools()
        self._use_llm = use_llm and HAS_OLLAMA
        self._graph = self._build_graph() if HAS_LANGGRAPH else None
        self._setup()
        if self._use_llm:
            logger.info("AI using Ollama LLM planner")
        else:
            logger.info("AI using rule-based planner")

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("planner", self._planner_node)
        builder.add_node("executor", partial(executor_node, tools=self.tools))
        builder.add_edge("planner", "executor")
        builder.add_edge("executor", END)
        builder.set_entry_point("planner")
        return builder.compile()

    def _planner_node(self, state: AgentState) -> AgentState:
        # Try LLM first, fall back to rule-based
        if self._use_llm:
            plan = _ollama_planner(state["intent"])
            if plan:
                state["plan"] = plan
                state["current_step"] = 0
                state["results"] = []
                state["error"] = None
                state["done"] = False
                logger.info("LLM plan for '%s': %s", state["intent"][:50], plan)
                return state
        return planner_node(state)

    def _setup(self):
        bus.subscribe("voice.command", self._on_voice, "ai-service")
        bus.subscribe("ai.intent", self._on_intent, "ai-service")

    def _on_voice(self, event: Event):
        action = event.payload.get("action", "")
        if action == "ai_query":
            text = event.payload.get("params", {}).get("text", "")
            self.process(text, {"source": "voice"})

    def _on_intent(self, event: Event):
        text = event.payload.get("text", "")
        params = event.payload.get("params", {})
        self.process(text, params)

    def process(self, text: str, params: Optional[dict] = None) -> AgentState:
        logger.info("AI intent: %s", text[:80])
        state: AgentState = {
            "intent": text,
            "params": params or {},
            "plan": [],
            "current_step": 0,
            "results": [],
            "error": None,
            "done": False,
        }

        if self._graph:
            state = self._graph.invoke(state)
        else:
            state = planner_node(state)
            state = executor_node(state, self.tools)

        bus.publish("ai.task.planned", {"intent": text, "plan": state["plan"]}, source="ai-service")
        bus.publish("ai.task.executed", {"intent": text, "results": state["results"], "error": state["error"]}, source="ai-service")

        logger.info("AI done: %s", state["results"] or state.get("error", "ok"))
        return state

    def shutdown(self):
        bus.unsubscribe("ai-service")
        logger.info("AI service stopped")
