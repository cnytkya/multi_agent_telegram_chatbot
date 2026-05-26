import pytest
from unittest.mock import AsyncMock

from src.agents.router import classify_intent
from src.llm.base import ChatMessage, LLMResponse


def _mock_llm(intent: str) -> AsyncMock:
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=LLMResponse(
        content=f'{{"intent": "{intent}"}}',
        model="mock",
        input_tokens=10,
        output_tokens=5,
    ))
    return llm


@pytest.mark.asyncio
@pytest.mark.parametrize("text,expected", [
    ("/task add buy milk", "tasks"),
    ("add task buy eggs", "tasks"),
    ("list tasks", "tasks"),
    ("write me an email", "writing"),
    ("draft a cover letter", "writing"),
])
async def test_keyword_routing(text: str, expected: str):
    llm = AsyncMock()
    result = await classify_intent(text, [], llm)
    assert result == expected
    llm.chat.assert_not_called()


@pytest.mark.asyncio
async def test_llm_routing_research():
    llm = _mock_llm("research")
    result = await classify_intent("What is the capital of France?", [], llm)
    assert result == "research"
    llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_llm_routing_fallback_on_bad_json():
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=LLMResponse(content="not json", model="mock", input_tokens=0, output_tokens=0))
    result = await classify_intent("something ambiguous", [], llm)
    assert result == "research"


@pytest.mark.asyncio
async def test_llm_routing_unknown_intent_falls_back():
    llm = _mock_llm("unknown_category")
    result = await classify_intent("hello there", [], llm)
    assert result == "research"


@pytest.mark.asyncio
async def test_history_passed_to_llm():
    llm = _mock_llm("clarify")
    history = [
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="assistant", content="hello"),
    ]
    result = await classify_intent("hmm", history, llm)
    assert result == "clarify"
    call_args = llm.chat.call_args
    messages_passed = call_args.kwargs["messages"] if call_args.kwargs else call_args.args[0]
    assert any(m.content == "hmm" for m in messages_passed)
