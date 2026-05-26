import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.session import get_session
from src.db.repository import upsert_user, get_or_create_conversation, append_message, get_recent_history
from src.agents.research import run_research_agent
from src.llm.factory import get_llm_provider
from src.observability.logging import configure_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    logger.info("app_starting", log_level=settings.log_level, llm_provider=settings.llm_provider)
    yield
    logger.info("app_stopped")


app = FastAPI(title="Multi-Agent Telegram Bot", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "0.1.0"})


class ChatRequest(BaseModel):
    telegram_id: int
    username: str | None = None
    message: str


class ChatResponse(BaseModel):
    reply: str
    agent: str
    input_tokens: int
    output_tokens: int


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, session: AsyncSession = Depends(get_session)) -> ChatResponse:
    llm = get_llm_provider()

    async with session.begin():
        user = await upsert_user(session, req.telegram_id, req.username)
        conv = await get_or_create_conversation(session, user.id)
        history = await get_recent_history(session, conv.id, limit=10)
        await append_message(session, conv.id, role="user", content=req.message)

        result = await run_research_agent(req.message, history, llm)

        await append_message(session, conv.id, role="assistant", content=result.content, agent="research")

    logger.info(
        "chat_complete",
        telegram_id=req.telegram_id,
        agent="research",
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )

    return ChatResponse(
        reply=result.content,
        agent="research",
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
