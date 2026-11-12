import pytest

from incident_intelligence.errors import StructuredOutputError
from incident_intelligence.extraction.schemas import Criticality
from incident_intelligence.extraction.service import EntityExtractionService


class FakeChain:
    def __init__(self, result: object) -> None:
        self.result = result
        self.received: dict[str, str] | None = None

    async def ainvoke(self, value: dict[str, str]) -> object:
        self.received = value
        return self.result


@pytest.mark.asyncio
async def test_process_text_returns_validated_result() -> None:
    chain = FakeChain(
        {
            "technologies": ["Kubernetes", "Redis"],
            "criticality": "alta",
            "technical_summary": "Redis agotó memoria y la API devuelve errores 503.",
        }
    )
    service = EntityExtractionService(chain)

    result = await service.process_text("  Redis agotó memoria en Kubernetes.  ")

    assert chain.received == {"text": "Redis agotó memoria en Kubernetes."}
    assert result.criticality is Criticality.HIGH
    assert result.technologies == ["Kubernetes", "Redis"]


@pytest.mark.asyncio
async def test_process_text_rejects_invalid_structured_output() -> None:
    service = EntityExtractionService(FakeChain({"technologies": []}))

    with pytest.raises(StructuredOutputError):
        await service.process_text("Fallo de Redis")


@pytest.mark.asyncio
async def test_process_text_rejects_empty_input() -> None:
    service = EntityExtractionService(FakeChain({}))

    with pytest.raises(ValueError, match="vacío"):
        await service.process_text("   ")
