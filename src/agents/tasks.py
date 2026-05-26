import json
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Task
from src.llm.base import ChatMessage, LLMProvider, LLMResponse

PARSE_SYSTEM = """You are a task manager parser. Extract a structured action from the user message.

Actions: add | list | done | delete

Respond with ONLY valid JSON:
- {"action": "add", "title": "<task title>"}
- {"action": "list"}
- {"action": "done", "id": <number>}
- {"action": "delete", "id": <number>}

If unsure, default to list."""


@dataclass
class TaskAction:
    action: str
    title: str | None = None
    task_id: int | None = None


async def _parse_action(user_message: str, llm: LLMProvider) -> TaskAction:
    response = await llm.chat(
        messages=[ChatMessage(role="user", content=user_message)],
        system=PARSE_SYSTEM,
        temperature=0.0,
        max_tokens=64,
    )
    try:
        data = json.loads(response.content.strip())
        action = data.get("action", "list")
        return TaskAction(action=action, title=data.get("title"), task_id=data.get("id"))
    except (json.JSONDecodeError, AttributeError):
        return TaskAction(action="list")


async def _execute_action(action: TaskAction, user_id: int, session: AsyncSession) -> str:
    if action.action == "add" and action.title:
        task = Task(user_id=user_id, title=action.title)
        session.add(task)
        await session.flush()
        return f"Added: {action.title} (#{task.id})"

    if action.action == "list":
        result = await session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at)
        )
        tasks = result.scalars().all()
        if not tasks:
            return "No tasks yet."
        lines = [f"{'[x]' if t.done else '[ ]'} #{t.id} {t.title}" for t in tasks]
        return "Your tasks:\n" + "\n".join(lines)

    if action.action == "done" and action.task_id:
        await session.execute(
            update(Task).where(Task.id == action.task_id, Task.user_id == user_id).values(done=True)
        )
        return f"Marked #{action.task_id} as done."

    if action.action == "delete" and action.task_id:
        result = await session.execute(
            select(Task).where(Task.id == action.task_id, Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if task:
            await session.delete(task)
            return f"Deleted #{action.task_id}."
        return f"Task #{action.task_id} not found."

    return "I didn't understand that task command. Try: add <title>, list, done <id>, delete <id>."


async def run_task_agent(
    user_message: str,
    history: list[ChatMessage],
    llm: LLMProvider,
    user_id: int,
    session: AsyncSession,
) -> LLMResponse:
    action = await _parse_action(user_message, llm)
    reply = await _execute_action(action, user_id, session)
    return LLMResponse(content=reply, model="deterministic", input_tokens=0, output_tokens=0)
