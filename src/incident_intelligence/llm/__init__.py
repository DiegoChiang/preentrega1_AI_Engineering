"""Clientes LLM intercambiables."""

from incident_intelligence.llm.base import BaseLLMClient
from incident_intelligence.llm.manager import AsyncLLMManager

__all__ = ["AsyncLLMManager", "BaseLLMClient"]

