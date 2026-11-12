"""Contrato de salida del pipeline técnico."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Criticality(StrEnum):
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"


class TechnicalEntityExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technologies: list[str] = Field(min_length=1, max_length=30)
    criticality: Criticality
    technical_summary: str = Field(min_length=10, max_length=2000)

    @field_validator("technologies")
    @classmethod
    def normalize_technologies(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            clean = value.strip()
            if clean and clean.casefold() not in seen:
                normalized.append(clean)
                seen.add(clean.casefold())
        if not normalized:
            raise ValueError("Debe existir al menos una tecnología")
        return normalized

