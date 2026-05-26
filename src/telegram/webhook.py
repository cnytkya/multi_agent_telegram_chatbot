import structlog
from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.repository import (
    append_message,
    get_or_create_conversation,
    get_recent_history,
    upsert_user,
)
from src.agents.graph import run_graph
from src.llm.factory import get_llm_provider
from src.telegram.client import send_message

logger = structlog.get_logger()


def _validate_secret(x_telegram_bot_api_secret_token: str | None) -> None:
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")


async def handle_update(request: Request, session: AsyncSession, secret_header: str | None) -> None:
    _validate_secret(secret_header)

    body = await request.json()
    message = body.get("message") or body.get("edited_message")
    if not message:
        return

    chat_id: int = message["chat"]["id"]
    text: str = message.get("text", "").strip()
    from_user = message.get("from", {})
    telegram_id: int = from_user.get("id", chat_id)
    username: str | None = from_user.get("username")

    if not text:
        return

    log = logger.bind(telegram_id=telegram_id, chat_id=chat_id)
    log.info("message_received", text_preview=text[:80])

    try:
        llm = get_llm_provider()

        async with session.begin():
            user = await upsert_user(session, telegram_id, username)
            conv = await get_or_create_conversation(session, user.id)
            history = await get_recent_history(session, conv.id, limit=10)
            await append_message(session, conv.id, role="user", content=text)

            result = await run_graph(text, history, llm)

            await append_message(session, conv.id, role="assistant", content=result.content, agent=result.agent)

        log.info("reply_ready", agent=result.agent, output_tokens=result.output_tokens)
        await send_message(chat_id, result.content)

    except Exception:
        log.exception("webhook_processing_error")
        await send_message(chat_id, "Sorry, something went wrong. Please try again.")
