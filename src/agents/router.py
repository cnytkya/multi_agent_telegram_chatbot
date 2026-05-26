import json
import re

from src.llm.base import ChatMessage, LLMProvider

SYSTEM_PROMPT = """You are a message router. Classify the user's intent into exactly one category.

Categories:
- research: factual questions, explanations, "what is", "how does", "why", general knowledge
- writing: drafting text, emails, summaries, social posts, rewrites, editing
- tasks: todo list operations — add, list, complete, delete tasks
- clarify: message is too ambiguous to classify

Respond with ONLY valid JSON: {"intent": "<category>"}"""


_KEYWORD_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^/task\b", re.IGNORECASE), "tasks"),
    (re.compile(r"\b(add task|list tasks?|done task|delete task|mark.*done)\b", re.IGNORECASE), "tasks"),
    (re.compile(r"\b(write|draft|compose|rewrite|summarize|edit)\b", re.IGNORECASE), "writing"),
]


def _keyword_route(text: str) -> str | None:
    for pattern, intent in _KEYWORD_RULES:
        if pattern.search(text):
            return intent
    return None


async def classify_intent(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
) -> str:
    fast_route = _keyword_route(user_message)
    if fast_route:
        return fast_route

    context_messages = list(history[-4:]) + [ChatMessage(role="user", content=user_message)]
    response = await llm.chat(
        messages=context_messages,
        system=SYSTEM_PROMPT,
        temperature=0.0,
        max_tokens=32,
    )

    try:
        data = json.loads(response.content.strip())
        intent = data.get("intent", "research")
        if intent not in ("research", "writing", "tasks", "clarify"):
            return "research"
        return intent
    except (json.JSONDecodeError, AttributeError):
        return "research"
