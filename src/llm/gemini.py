import google.generativeai as genai

from src.config import settings
from src.llm.base import ChatMessage, LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.llm_model or "gemini-1.5-flash"

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system,
            generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
        )

        history = []
        last_user_msg = ""
        for m in messages:
            if m.role == "system":
                continue
            if m.role == "user":
                last_user_msg = m.content
                history.append({"role": "user", "parts": [m.content]})
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        chat = model.start_chat(history=history[:-1] if history else [])
        response = await chat.send_message_async(last_user_msg)

        return LLMResponse(
            content=response.text,
            model=self._model_name,
            input_tokens=0,
            output_tokens=0,
        )
