"""Interfaz común para proveedores LLM."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence

from incident_intelligence.schemas import ChatMessage, ModelConfig, ModelResponse


class BaseLLMClient(ABC):
    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(self, messages: Sequence[ChatMessage]) -> ModelResponse:
        """Genera una respuesta completa sin bloquear el event loop."""

    @abstractmethod
    def stream(self, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        """Entrega fragmentos de texto conforme llegan del proveedor."""

    @staticmethod
    def require_messages(messages: Sequence[ChatMessage]) -> None:
        if not messages:
            raise ValueError("Se requiere al menos un mensaje")

