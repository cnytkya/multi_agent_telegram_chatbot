import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.research import run_research_agent
from src.agents.writing import run_writing_agent
from src.llm.base import ChatMessage, LLMResponse


def _llm(content: str = "test reply") -> AsyncMock:
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=LLMResponse(content=content, model="mock", input_tokens=10, output_tokens=5))
    return llm


@pytest.mark.asyncio
async def test_research_agent_passes_user_message():
    llm = _llm("Paris is the capital of France.")
    result = await run_research_agent("Capital of France?", [], llm)
    assert result.content == "Paris is the capital of France."
    call_args = llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args.args[0]
    assert messages[-1].role == "user"
    assert "France" in messages[-1].content


@pytest.mark.asyncio
async def test_research_agent_includes_history():
    llm = _llm("answer")
    history = [ChatMessage(role="user", content="prior"), ChatMessage(role="assistant", content="response")]
    await run_research_agent("follow-up", history, llm)
    messages = llm.chat.call_args.kwargs.get("messages") or llm.chat.call_args.args[0]
    assert len(messages) == 3
    assert messages[0].content == "prior"


@pytest.mark.asyncio
async def test_writing_agent_uses_higher_temperature():
    llm = _llm("draft text")
    await run_writing_agent("write an email", [], llm)
    call_kwargs = llm.chat.call_args.kwargs
    assert call_kwargs.get("temperature", 0) >= 0.5


@pytest.mark.asyncio
async def test_research_agent_uses_low_temperature():
    llm = _llm("factual answer")
    await run_research_agent("what is gravity?", [], llm)
    call_kwargs = llm.chat.call_args.kwargs
    assert call_kwargs.get("temperature", 1) <= 0.5
