import importlib
import time

from app.core.config import get_settings
from app.infrastructure.llm.base import LLMConfig, LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        self._genai = importlib.import_module("google.generativeai")
        settings = get_settings()
        self._genai.configure(api_key=settings.GEMINI_API_KEY or "sk-placeholder")
        self._name = "gemini"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        start = time.monotonic()
        model = self._genai.GenerativeModel(
            model_name=config.model,
            system_instruction=config.system_prompt,
            generation_config=self._genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            ),
        )
        response = await model.generate_content_async(prompt)
        elapsed = int((time.monotonic() - start) * 1000)

        token_counts = response.usage_metadata if hasattr(response, "usage_metadata") and response.usage_metadata else None

        return LLMResponse(
            content=response.text or "",
            model=config.model,
            prompt_tokens=token_counts.prompt_token_count if token_counts else 0,
            completion_tokens=token_counts.candidates_token_count if token_counts else 0,
            total_tokens=(token_counts.prompt_token_count + token_counts.candidates_token_count) if token_counts else 0,
            latency_ms=elapsed,
        )

    async def health_check(self) -> bool:
        try:
            settings = get_settings()
            model_name = settings.GEMINI_MODEL or "gemini-2.5-flash-001"
            self._genai.get_model(f"models/{model_name}")
            return True
        except Exception:
            return False
