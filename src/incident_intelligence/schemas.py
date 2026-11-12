"""Contratos de datos compartidos por los clientes LLM."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Provider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: MessageRole
    content: str = Field(min_length=1, max_length=100_000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El contenido no puede estar vacío")
        return value


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Provider
    model: str = Field(min_length=1)
    temperature: float | None = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1200, ge=1, le=128_000)
    timeout_seconds: float = Field(default=45, gt=0, le=600)
    max_retries: int = Field(default=3, ge=1, le=10)

    @field_validator("model")
    @classmethod
    def model_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El modelo no puede estar vacío")
        return value


class TokenUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    provider: Provider
    model: str
    finish_reason: str | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)

