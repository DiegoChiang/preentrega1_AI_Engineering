from types import SimpleNamespace

import pytest

from incident_intelligence.errors import LLMProviderError
from incident_intelligence.llm.anthropic_client import AnthropicClient
from incident_intelligence.llm.openai_client import OpenAIClient
from incident_intelligence.schemas import ChatMessage, MessageRole, ModelConfig, Provider


class AsyncTokens:
    def __init__(self, values: list[object]) -> None:
        self._values = iter(values)

    def __aiter__(self) -> "AsyncTokens":
        return self

    async def __anext__(self) -> object:
        try:
            return next(self._values)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeOpenAICompletions:
    async def create(self, **kwargs: object) -> object:
        if kwargs.get("stream"):
            return AsyncTokens(
                [
                    SimpleNamespace(
                        choices=[SimpleNamespace(delta=SimpleNamespace(content="Hola "))]
                    ),
                    SimpleNamespace(
                        choices=[SimpleNamespace(delta=SimpleNamespace(content="mundo"))]
                    ),
                ]
            )
        return SimpleNamespace(
            id="response-1",
            model="gpt-test",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Respuesta completa"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=5),
        )


class FakeOpenAISDK:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeOpenAICompletions())


class FailingOpenAICompletions:
    async def create(self, **kwargs: object) -> object:
        raise ConnectionError("servicio no disponible")


class FailingOpenAISDK:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FailingOpenAICompletions())


class InterruptedOpenAIStream:
    def __init__(self) -> None:
        self._position = 0

    def __aiter__(self) -> "InterruptedOpenAIStream":
        return self

    async def __anext__(self) -> object:
        if self._position == 0:
            self._position += 1
            return SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content="Parcial"))]
            )
        raise ConnectionError("stream interrumpido")


class InterruptedOpenAICompletions:
    def __init__(self) -> None:
        self.calls = 0

    async def create(self, **kwargs: object) -> object:
        self.calls += 1
        return InterruptedOpenAIStream()


class InterruptedOpenAISDK:
    def __init__(self) -> None:
        self.completions = InterruptedOpenAICompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class RecoveringOpenAICompletions:
    def __init__(self) -> None:
        self.calls = 0

    async def create(self, **kwargs: object) -> object:
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("límite temporal")
        return AsyncTokens(
            [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Listo"))])]
        )


class RecoveringOpenAISDK:
    def __init__(self) -> None:
        self.completions = RecoveringOpenAICompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class FakeAnthropicStream:
    def __init__(self) -> None:
        self.text_stream = AsyncTokens(["Uno ", "dos"])

    async def __aenter__(self) -> "FakeAnthropicStream":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeAnthropicMessages:
    def __init__(self) -> None:
        self.create_payload: dict[str, object] | None = None
        self.stream_payload: dict[str, object] | None = None

    async def create(self, **kwargs: object) -> object:
        self.create_payload = kwargs
        return SimpleNamespace(
            id="message-1",
            model="claude-test",
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text="Respuesta Anthropic")],
            usage=SimpleNamespace(input_tokens=9, output_tokens=4),
        )

    def stream(self, **kwargs: object) -> FakeAnthropicStream:
        self.stream_payload = kwargs
        return FakeAnthropicStream()


class FakeAnthropicSDK:
    def __init__(self) -> None:
        self.messages = FakeAnthropicMessages()


class FailingAnthropicMessages:
    async def create(self, **kwargs: object) -> object:
        raise TimeoutError("tiempo de espera agotado")


class FailingAnthropicSDK:
    def __init__(self) -> None:
        self.messages = FailingAnthropicMessages()


def messages() -> list[ChatMessage]:
    return [
        ChatMessage(role=MessageRole.SYSTEM, content="Sé preciso."),
        ChatMessage(role=MessageRole.USER, content="Pregunta"),
    ]


@pytest.mark.asyncio
async def test_openai_generation_maps_response_and_usage() -> None:
    client = OpenAIClient(
        ModelConfig(provider=Provider.OPENAI, model="gpt-test"),
        sdk_client=FakeOpenAISDK(),
    )

    result = await client.generate(messages())

    assert result.content == "Respuesta completa"
    assert result.provider is Provider.OPENAI
    assert result.usage.total_tokens == 17
    assert result.raw_metadata == {"response_id": "response-1"}


@pytest.mark.asyncio
async def test_openai_stream_emits_incremental_text() -> None:
    client = OpenAIClient(
        ModelConfig(provider=Provider.OPENAI, model="gpt-test"),
        sdk_client=FakeOpenAISDK(),
    )

    tokens = [token async for token in client.stream(messages())]

    assert tokens == ["Hola ", "mundo"]


@pytest.mark.asyncio
async def test_anthropic_separates_system_message_and_streams() -> None:
    sdk = FakeAnthropicSDK()
    client = AnthropicClient(
        ModelConfig(provider=Provider.ANTHROPIC, model="claude-test"),
        sdk_client=sdk,
    )

    result = await client.generate(messages())
    tokens = [token async for token in client.stream(messages())]

    assert result.content == "Respuesta Anthropic"
    assert result.usage.total_tokens == 13
    assert sdk.messages.create_payload is not None
    assert sdk.messages.create_payload["system"] == "Sé preciso."
    assert sdk.messages.create_payload["messages"] == [{"role": "user", "content": "Pregunta"}]
    assert "temperature" not in sdk.messages.create_payload
    assert tokens == ["Uno ", "dos"]


@pytest.mark.asyncio
async def test_openai_failure_uses_domain_error() -> None:
    client = OpenAIClient(
        ModelConfig(provider=Provider.OPENAI, model="gpt-test", max_retries=1),
        sdk_client=FailingOpenAISDK(),
    )

    with pytest.raises(LLMProviderError, match="OpenAI no pudo completar"):
        await client.generate(messages())


@pytest.mark.asyncio
async def test_anthropic_failure_uses_domain_error() -> None:
    client = AnthropicClient(
        ModelConfig(provider=Provider.ANTHROPIC, model="claude-test", max_retries=1),
        sdk_client=FailingAnthropicSDK(),
    )

    with pytest.raises(LLMProviderError, match="Anthropic no pudo completar"):
        await client.generate(messages())


@pytest.mark.asyncio
async def test_stream_does_not_retry_after_emitting_text() -> None:
    sdk = InterruptedOpenAISDK()
    client = OpenAIClient(
        ModelConfig(provider=Provider.OPENAI, model="gpt-test", max_retries=3),
        sdk_client=sdk,
    )
    stream = client.stream(messages())

    assert await anext(stream) == "Parcial"
    with pytest.raises(LLMProviderError, match="streaming de OpenAI"):
        await anext(stream)
    assert sdk.completions.calls == 1


@pytest.mark.asyncio
async def test_stream_retries_before_first_text() -> None:
    sdk = RecoveringOpenAISDK()
    client = OpenAIClient(
        ModelConfig(provider=Provider.OPENAI, model="gpt-test", max_retries=2),
        sdk_client=sdk,
    )

    tokens = [token async for token in client.stream(messages())]

    assert tokens == ["Listo"]
    assert sdk.completions.calls == 2
