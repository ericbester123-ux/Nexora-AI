import importlib
import time

from app.core.config import get_settings
from app.infrastructure.llm.base import LLMConfig, LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        self._anthropic = importlib.import_module("anthropic")
        settings = get_settings()
        self._client = self._anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY or "sk-placeholder",
        )
        self._name = "claude"

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        start = time.monotonic()
        response = await self._client.messages.create(
            model=config.model,
            system=config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )
        elapsed = int((time.monotonic() - start) * 1000)

        content = ""
        if response.content:
            for block in response.content:
                if block.type == "text":
                    content = block.text
                    break

        return LLMResponse(
            content=content or "",
            model=config.model,
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
            latency_ms=elapsed,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
