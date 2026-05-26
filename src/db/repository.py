from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.db.models import Conversation, Message, User
from src.llm.base import ChatMessage


async def upsert_user(session: AsyncSession, telegram_id: int, username: str | None = None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
    elif username and user.username != username:
        user.username = username
        await session.flush()
    return user


async def get_or_create_conversation(session: AsyncSession, user_id: int) -> Conversation:
    result = await session.execute(
        select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.started_at.desc()).limit(1)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        conv = Conversation(user_id=user_id)
        session.add(conv)
        await session.flush()
    return conv


async def append_message(
    session: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    agent: str | None = None,
) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content, agent=agent)
    session.add(msg)
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(last_message_at=func.now())
    )
    await session.flush()
    return msg


async def get_recent_history(
    session: AsyncSession,
    conversation_id: int,
    limit: int = 10,
) -> list[ChatMessage]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [ChatMessage(role=r.role, content=r.content) for r in reversed(rows)]
