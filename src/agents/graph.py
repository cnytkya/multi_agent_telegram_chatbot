from dataclasses import dataclass

from src.agents.research import run_research_agent
from src.llm.base import ChatMessage, LLMProvider


@dataclass
class GraphResult:
    content: str
    agent: str
    input_tokens: int
    output_tokens: int


async def run_graph(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
) -> GraphResult:
    # Placeholder: routes everything to Research Agent until Step 6 adds the full Router + LangGraph.
    result = await run_research_agent(user_message, history, llm)
    return GraphResult(
        content=result.content,
        agent="research",
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
