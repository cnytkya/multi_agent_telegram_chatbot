import httpx
import structlog

from src.config import settings

logger = structlog.get_logger()

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


async def send_message(chat_id: int, text: str) -> None:
    url = TELEGRAM_API.format(token=settings.telegram_bot_token, method="sendMessage")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        if not resp.is_success:
            logger.error("telegram_send_failed", chat_id=chat_id, status=resp.status_code, body=resp.text)


async def set_webhook(url: str, secret: str) -> bool:
    api_url = TELEGRAM_API.format(token=settings.telegram_bot_token, method="setWebhook")
    async with httpx.AsyncClient() as client:
        resp = await client.post(api_url, json={"url": url, "secret_token": secret}, timeout=10)
        data = resp.json()
        logger.info("webhook_set", ok=data.get("ok"), description=data.get("description"))
        return data.get("ok", False)
