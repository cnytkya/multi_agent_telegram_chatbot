from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str = Field(default="")
    telegram_webhook_secret: str = Field(default="")
    telegram_webhook_url: str = Field(default="")

    # LLM
    llm_provider: str = Field(default="anthropic")
    anthropic_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    llm_model: str = Field(default="claude-sonnet-4-6")

    # Database
    database_url: str = Field(default="postgresql+asyncpg://bot:bot@db:5432/bot")

    # App
    log_level: str = Field(default="INFO")


settings = Settings()
