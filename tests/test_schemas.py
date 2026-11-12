import pytest
from pydantic import ValidationError

from incident_intelligence.schemas import ChatMessage, MessageRole, ModelConfig, Provider


def test_chat_message_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(role=MessageRole.USER, content="   ")


def test_model_config_validates_limits() -> None:
    with pytest.raises(ValidationError):
        ModelConfig(provider=Provider.OPENAI, model="gpt", max_retries=0)


@pytest.mark.parametrize("temperature", [-0.01, 2.01])
def test_model_config_rejects_temperature_outside_supported_range(
    temperature: float,
) -> None:
    with pytest.raises(ValidationError):
        ModelConfig(provider=Provider.OPENAI, model="gpt", temperature=temperature)


def test_model_config_rejects_blank_model() -> None:
    with pytest.raises(ValidationError):
        ModelConfig(provider=Provider.OPENAI, model="   ")
