import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMConfig:
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    retry_count: int = 2
    timeout: int = 60
    system_prompt: str = "You are an expert freelance proposal writer."


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
