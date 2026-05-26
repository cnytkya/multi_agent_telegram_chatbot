import ollama as ollama_sdk

from src.config import settings
from src.llm.base import ChatMessage, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(self) -> None:
        self._client = ollama_sdk.AsyncClient(host=settings.ollama_base_url)
        self._model = settings.llm_model or "llama3.2"

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        api_messages: list[dict] = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages += [{"role": m.role, "content": m.content} for m in messages]

        response = await self._client.chat(
            model=self._model,
            messages=api_messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )

        content = response.message.content or ""
        input_tokens = response.prompt_eval_count or 0
        output_tokens = response.eval_count or 0

        return LLMResponse(
            content=content,
            model=self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
