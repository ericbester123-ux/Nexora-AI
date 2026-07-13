import time

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.infrastructure.llm.base import LLMConfig, LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY or "sk-placeholder",
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self._name = "deepseek"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        start = time.monotonic()
        response = await self._client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )
        elapsed = int((time.monotonic() - start) * 1000)

        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice else ""

        return LLMResponse(
            content=content or "",
            model=config.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            latency_ms=elapsed,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
