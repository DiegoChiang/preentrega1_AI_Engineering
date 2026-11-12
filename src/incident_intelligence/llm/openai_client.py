"""Adaptador asíncrono para OpenAI."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import Any

from incident_intelligence.certificates import configure_system_certificate_store
from incident_intelligence.errors import LLMProviderError
from incident_intelligence.llm.base import BaseLLMClient
from incident_intelligence.retry import retry_async
from incident_intelligence.schemas import (
    ChatMessage,
    ModelConfig,
    ModelResponse,
    Provider,
    TokenUsage,
)


class OpenAIClient(BaseLLMClient):
    def __init__(
        self,
        config: ModelConfig,
        *,
        api_key: str | None = None,
        sdk_client: Any | None = None,
    ) -> None:
        super().__init__(config)
        if config.provider is not Provider.OPENAI:
            raise ValueError("OpenAIClient requiere provider='openai'")
        if sdk_client is None:
            configure_system_certificate_store()
            try:
                from openai import AsyncOpenAI
            except ImportError as exc:  # pragma: no cover - depende del entorno
                raise RuntimeError("Instala la dependencia 'openai'") from exc
            sdk_client = AsyncOpenAI(
                api_key=api_key,
                timeout=config.timeout_seconds,
                max_retries=0,
            )
        self._client = sdk_client

    def _request(self, messages: Sequence[ChatMessage]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [message.model_dump(mode="json") for message in messages],
            "max_completion_tokens": self.config.max_tokens,
        }
        if self.config.temperature is not None and not self.config.model.startswith(
            ("gpt-5", "o")
        ):
            payload["temperature"] = self.config.temperature
        return payload

    async def generate(self, messages: Sequence[ChatMessage]) -> ModelResponse:
        self.require_messages(messages)

        async def call() -> Any:
            return await self._client.chat.completions.create(**self._request(messages))

        try:
            response = await retry_async(call, attempts=self.config.max_retries)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise LLMProviderError(f"OpenAI no pudo completar la solicitud: {exc}") from exc

        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return ModelResponse(
            content=choice.message.content or "",
            provider=Provider.OPENAI,
            model=getattr(response, "model", self.config.model),
            finish_reason=getattr(choice, "finish_reason", None),
            usage=TokenUsage(
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            raw_metadata={"response_id": getattr(response, "id", None)},
        )

    async def stream(self, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        self.require_messages(messages)
        emitted = False
        for attempt in range(1, self.config.max_retries + 1):
            try:
                stream = await self._client.chat.completions.create(
                    **self._request(messages), stream=True
                )
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    text = chunk.choices[0].delta.content
                    if text:
                        emitted = True
                        yield text
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if emitted or attempt == self.config.max_retries:
                    raise LLMProviderError(f"Falló el streaming de OpenAI: {exc}") from exc
                await asyncio.sleep(0.25 * (2 ** (attempt - 1)))

