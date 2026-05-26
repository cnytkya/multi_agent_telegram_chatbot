import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config import settings
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
