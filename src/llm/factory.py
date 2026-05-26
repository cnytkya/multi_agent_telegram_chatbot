from src.config import settings
from src.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "gemini":
        from src.llm.gemini import GeminiProvider
        return GeminiProvider()

    if settings.llm_provider == "ollama":
        from src.llm.ollama import OllamaProvider
        return OllamaProvider()

    from src.llm.anthropic import AnthropicProvider
    return AnthropicProvider()
