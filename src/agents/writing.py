from src.llm.base import ChatMessage, LLMProvider, LLMResponse

SYSTEM_PROMPT = """You are an expert writing assistant. Help users draft, edit, and refine text.

- If the request lacks key details (audience, tone, length), ask one focused clarifying question.
- Otherwise produce the draft immediately, then offer to revise.
- Match the requested register: professional for emails, casual for social posts, etc.
- Keep your own explanatory text minimal — lead with the content."""


async def run_writing_agent(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
) -> LLMResponse:
    messages = list(history) + [ChatMessage(role="user", content=user_message)]
    return await llm.chat(messages=messages, system=SYSTEM_PROMPT, temperature=0.7, max_tokens=1500)
