from src.llm.base import ChatMessage, LLMProvider, LLMResponse

SYSTEM_PROMPT = """You are a knowledgeable research assistant. Answer questions accurately and concisely.
If you are uncertain about something, say so clearly rather than guessing.
Keep answers focused and practical. Use plain text — no markdown unless the user asks."""


async def run_research_agent(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
) -> LLMResponse:
    messages = list(history) + [ChatMessage(role="user", content=user_message)]
    return await llm.chat(messages=messages, system=SYSTEM_PROMPT, temperature=0.3, max_tokens=1024)
