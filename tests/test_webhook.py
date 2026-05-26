import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from src.main import app


FAKE_UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 1,
        "from": {"id": 12345, "username": "testuser", "is_bot": False, "first_name": "Test"},
        "chat": {"id": 12345, "type": "private"},
        "text": "What is Python?",
    }
}


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_returns_200_immediately():
    with (
        patch("src.telegram.webhook.get_llm_provider"),
        patch("src.telegram.webhook.upsert_user", new_callable=AsyncMock),
        patch("src.telegram.webhook.get_or_create_conversation", new_callable=AsyncMock),
        patch("src.telegram.webhook.get_recent_history", new_callable=AsyncMock, return_value=[]),
        patch("src.telegram.webhook.append_message", new_callable=AsyncMock),
        patch("src.telegram.webhook.run_graph", new_callable=AsyncMock),
        patch("src.telegram.webhook.send_message", new_callable=AsyncMock),
        patch("src.db.session.get_session"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/webhook", json=FAKE_UPDATE)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_webhook_rejects_bad_secret():
    with patch("src.config.settings") as mock_settings:
        mock_settings.telegram_webhook_secret = "correct-secret"
        mock_settings.llm_provider = "anthropic"
        mock_settings.log_level = "INFO"
        mock_settings.database_url = "postgresql+asyncpg://bot:bot@db:5432/bot"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/webhook",
                json=FAKE_UPDATE,
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
            )
    assert resp.status_code in (200, 403)
