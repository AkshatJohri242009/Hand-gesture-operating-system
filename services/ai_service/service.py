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


class AIService:
    def __init__(self):
        self.tools = AgentTools()
        self._graph = self._build_graph() if HAS_LANGGRAPH else None
        self._setup()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("planner", planner_node)
        builder.add_node("executor", partial(executor_node, tools=self.tools))
        builder.add_edge("planner", "executor")
        builder.add_edge("executor", END)
        builder.set_entry_point("planner")
        return builder.compile()

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
