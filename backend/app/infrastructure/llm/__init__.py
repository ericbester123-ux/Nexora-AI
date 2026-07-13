from app.core.config import get_settings
from app.infrastructure.llm.base import LLMConfig, LLMProvider, LLMResponse
from app.infrastructure.llm.openai_provider import OpenAIProvider


def _resolve_model(settings) -> str:
    provider = settings.LLM_PROVIDER.lower()
    models = {
        "openai": settings.LLM_MODEL or "gpt-4o-mini",
        "claude": settings.ANTHROPIC_MODEL,
        "gemini": settings.GEMINI_MODEL,
        "deepseek": settings.DEEPSEEK_MODEL,
    }
    model = models.get(provider)
    if not model:
        raise ValueError(
            f"No model configured for provider '{settings.LLM_PROVIDER}'. "
            f"Set the corresponding <PROVIDER>_MODEL environment variable."
        )
    return model


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider_name = settings.LLM_PROVIDER.lower()

    # Validate model availability before constructing the provider
    _resolve_model(settings)

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "claude":
        from app.infrastructure.llm.claude_provider import ClaudeProvider
        return ClaudeProvider()
    elif provider_name == "gemini":
        from app.infrastructure.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    elif provider_name == "deepseek":
        from app.infrastructure.llm.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider '{settings.LLM_PROVIDER}'. "
            f"Available: openai, claude, gemini, deepseek"
        )


def make_llm_config(settings=None) -> LLMConfig:
    if settings is None:
        settings = get_settings()
    return LLMConfig(
        model=_resolve_model(settings),
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        top_p=settings.LLM_TOP_P,
        retry_count=settings.LLM_RETRY_COUNT,
        timeout=settings.LLM_TIMEOUT,
        system_prompt=settings.LLM_SYSTEM_PROMPT,
    )


__all__ = ["LLMConfig", "LLMProvider", "LLMResponse", "OpenAIProvider", "DeepSeekProvider", "get_llm_provider", "make_llm_config"]
