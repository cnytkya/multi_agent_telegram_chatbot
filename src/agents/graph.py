from dataclasses import dataclass
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.research import run_research_agent
from src.agents.router import classify_intent
from src.agents.writing import run_writing_agent
from src.agents.tasks import run_task_agent
from src.llm.base import ChatMessage, LLMProvider


@dataclass
class GraphResult:
    content: str
    agent: str
    input_tokens: int
    output_tokens: int


class AgentState(TypedDict):
    user_message: str
    history: list[ChatMessage]
    intent: str
    reply: str
    agent: str
    input_tokens: int
    output_tokens: int
    user_id: int
    session: AsyncSession | None
    llm: LLMProvider


def _build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    async def router_node(state: AgentState) -> dict:
        intent = await classify_intent(state["user_message"], state["history"], state["llm"])
        return {"intent": intent}

    async def research_node(state: AgentState) -> dict:
        result = await run_research_agent(state["user_message"], state["history"], state["llm"])
        return {"reply": result.content, "agent": "research", "input_tokens": result.input_tokens, "output_tokens": result.output_tokens}

    async def writing_node(state: AgentState) -> dict:
        result = await run_writing_agent(state["user_message"], state["history"], state["llm"])
        return {"reply": result.content, "agent": "writing", "input_tokens": result.input_tokens, "output_tokens": result.output_tokens}

    async def tasks_node(state: AgentState) -> dict:
        result = await run_task_agent(
            state["user_message"],
            state["history"],
            state["llm"],
            state["user_id"],
            state["session"],
        )
        return {"reply": result.content, "agent": "tasks", "input_tokens": result.input_tokens, "output_tokens": result.output_tokens}

    async def clarify_node(state: AgentState) -> dict:
        return {
            "reply": "I'm not sure what you'd like help with. You can ask me a question, ask me to write something, or manage your task list.",
            "agent": "clarify",
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def route_after_router(state: AgentState) -> str:
        return state["intent"]

    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("writing", writing_node)
    graph.add_node("tasks", tasks_node)
    graph.add_node("clarify", clarify_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {"research": "research", "writing": "writing", "tasks": "tasks", "clarify": "clarify"},
    )
    graph.add_edge("research", END)
    graph.add_edge("writing", END)
    graph.add_edge("tasks", END)
    graph.add_edge("clarify", END)

    return graph.compile()


_compiled_graph = _build_graph()


async def run_graph(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
    user_id: int = 0,
    session: AsyncSession | None = None,
) -> GraphResult:
    final_state = await _compiled_graph.ainvoke({
        "user_message": user_message,
        "history": history,
        "intent": "",
        "reply": "",
        "agent": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "user_id": user_id,
        "session": session,
        "llm": llm,
    })
    return GraphResult(
        content=final_state["reply"],
        agent=final_state["agent"],
        input_tokens=final_state["input_tokens"],
        output_tokens=final_state["output_tokens"],
    )
