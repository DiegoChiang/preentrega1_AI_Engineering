"""Adaptador asíncrono para Anthropic."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import Any

from incident_intelligence.certificates import configure_system_certificate_store
from incident_intelligence.errors import LLMProviderError
from incident_intelligence.llm.base import BaseLLMClient
from incident_intelligence.retry import retry_async
from incident_intelligence.schemas import (
    ChatMessage,
    MessageRole,
    ModelConfig,
    ModelResponse,
    Provider,
    TokenUsage,
)


class AnthropicClient(BaseLLMClient):
    def __init__(
        self,
        config: ModelConfig,
        *,
        api_key: str | None = None,
        sdk_client: Any | None = None,
    ) -> None:
        super().__init__(config)
        if config.provider is not Provider.ANTHROPIC:
            raise ValueError("AnthropicClient requiere provider='anthropic'")
        if sdk_client is None:
            configure_system_certificate_store()
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise RuntimeError("Instala la dependencia 'anthropic'") from exc
            sdk_client = AsyncAnthropic(
                api_key=api_key,
                timeout=config.timeout_seconds,
                max_retries=0,
            )
        self._client = sdk_client

    def _request(self, messages: Sequence[ChatMessage]) -> dict[str, Any]:
        systems = [message.content for message in messages if message.role is MessageRole.SYSTEM]
        conversation = [
            {"role": message.role.value, "content": message.content}
            for message in messages
            if message.role is not MessageRole.SYSTEM
        ]
        if not conversation:
            raise ValueError("Anthropic requiere al menos un mensaje user o assistant")
        payload: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": conversation,
        }
        if systems:
            payload["system"] = "\n\n".join(systems)
        return payload

    async def generate(self, messages: Sequence[ChatMessage]) -> ModelResponse:
        self.require_messages(messages)

        async def call() -> Any:
            return await self._client.messages.create(**self._request(messages))

        try:
            response = await retry_async(call, attempts=self.config.max_retries)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise LLMProviderError(f"Anthropic no pudo completar la solicitud: {exc}") from exc

        content = "".join(
            getattr(block, "text", "")
            for block in response.content
            if getattr(block, "type", None) == "text"
        )
        usage = getattr(response, "usage", None)
        return ModelResponse(
            content=content,
            provider=Provider.ANTHROPIC,
            model=getattr(response, "model", self.config.model),
            finish_reason=getattr(response, "stop_reason", None),
            usage=TokenUsage(
                input_tokens=getattr(usage, "input_tokens", 0) or 0,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
            ),
            raw_metadata={"response_id": getattr(response, "id", None)},
        )

    async def stream(self, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        self.require_messages(messages)
        emitted = False
        for attempt in range(1, self.config.max_retries + 1):
            try:
                async with self._client.messages.stream(**self._request(messages)) as stream:
                    async for text in stream.text_stream:
                        if text:
                            emitted = True
                            yield text
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if emitted or attempt == self.config.max_retries:
                    raise LLMProviderError(f"Falló el streaming de Anthropic: {exc}") from exc
                await asyncio.sleep(0.25 * (2 ** (attempt - 1)))

