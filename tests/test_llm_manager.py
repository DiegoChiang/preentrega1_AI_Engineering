from collections.abc import AsyncIterator, Sequence

import pytest

from incident_intelligence.config import Settings
from incident_intelligence.errors import LLMConfigurationError
from incident_intelligence.llm.base import BaseLLMClient
from incident_intelligence.llm.manager import AsyncLLMManager
from incident_intelligence.schemas import ChatMessage, ModelConfig, ModelResponse, Provider


class FakeClient(BaseLLMClient):
    def __init__(self, config: ModelConfig, key: str) -> None:
        super().__init__(config)
        self.key = key

    async def generate(self, messages: Sequence[ChatMessage]) -> ModelResponse:
        return ModelResponse(content="ok", provider=self.config.provider, model=self.config.model)

    async def stream(self, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        yield "ok"


def fake_factory(config: ModelConfig, key: str) -> BaseLLMClient:
    return FakeClient(config, key)


def test_manager_selects_openai_and_shared_configuration() -> None:
    settings = Settings(
        openai_api_key="secret-openai",
        anthropic_api_key="secret-anthropic",
        llm_temperature=0.4,
        llm_max_retries=4,
    )
    manager = AsyncLLMManager(
        settings,
        factories={Provider.OPENAI: fake_factory, Provider.ANTHROPIC: fake_factory},
    )

    client = manager.create("openai")

    assert isinstance(client, FakeClient)
    assert client.config.provider is Provider.OPENAI
    assert client.config.temperature == 0.4
    assert client.config.max_retries == 4
    assert client.key == "secret-openai"


def test_manager_selects_anthropic() -> None:
    settings = Settings(openai_api_key="one", anthropic_api_key="two")
    manager = AsyncLLMManager(
        settings,
        factories={Provider.OPENAI: fake_factory, Provider.ANTHROPIC: fake_factory},
    )

    client = manager.create(Provider.ANTHROPIC)

    assert client.config.provider is Provider.ANTHROPIC
    assert client.key == "two"


def test_manager_reports_missing_provider_key_as_configuration_error() -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key=None,
        anthropic_api_key=None,
    )
    manager = AsyncLLMManager(settings, factories={Provider.OPENAI: fake_factory})

    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY"):
        manager.create(Provider.OPENAI)


def test_manager_rejects_unknown_provider() -> None:
    settings = Settings(_env_file=None, openai_api_key="one")
    manager = AsyncLLMManager(settings, factories={Provider.OPENAI: fake_factory})

    with pytest.raises(LLMConfigurationError, match="Proveedor no soportado"):
        manager.create("unsupported")
