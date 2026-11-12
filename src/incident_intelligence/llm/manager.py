"""Selección dinámica del proveedor LLM."""

from collections.abc import Callable

from incident_intelligence.config import Settings
from incident_intelligence.errors import LLMConfigurationError
from incident_intelligence.llm.anthropic_client import AnthropicClient
from incident_intelligence.llm.base import BaseLLMClient
from incident_intelligence.llm.openai_client import OpenAIClient
from incident_intelligence.schemas import ModelConfig, Provider

ClientFactory = Callable[[ModelConfig, str], BaseLLMClient]


def _openai_factory(config: ModelConfig, api_key: str) -> BaseLLMClient:
    return OpenAIClient(config, api_key=api_key)


def _anthropic_factory(config: ModelConfig, api_key: str) -> BaseLLMClient:
    return AnthropicClient(config, api_key=api_key)


class AsyncLLMManager:
    """Construye clientes intercambiables a partir de una configuración común."""

    def __init__(
        self,
        settings: Settings,
        *,
        factories: dict[Provider, ClientFactory] | None = None,
    ) -> None:
        self.settings = settings
        self.factories = factories or {
            Provider.OPENAI: _openai_factory,
            Provider.ANTHROPIC: _anthropic_factory,
        }

    def create(self, provider: Provider | str | None = None) -> BaseLLMClient:
        try:
            selected = Provider(provider or self.settings.llm_provider)
        except ValueError as exc:
            raise LLMConfigurationError(f"Proveedor no soportado: {provider}") from exc

        model = (
            self.settings.openai_model
            if selected is Provider.OPENAI
            else self.settings.anthropic_model
        )
        config = ModelConfig(
            provider=selected,
            model=model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            timeout_seconds=self.settings.llm_timeout_seconds,
            max_retries=self.settings.llm_max_retries,
        )
        try:
            key = self.settings.require_provider_key(selected.value)
        except ValueError as exc:
            raise LLMConfigurationError(str(exc)) from exc
        try:
            factory = self.factories[selected]
        except KeyError as exc:
            raise LLMConfigurationError(f"No existe una fábrica para {selected.value}") from exc
        return factory(config, key)

