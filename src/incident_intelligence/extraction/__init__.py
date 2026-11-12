"""Extracción estructurada de entidades técnicas."""

from incident_intelligence.extraction.schemas import Criticality, TechnicalEntityExtraction
from incident_intelligence.extraction.service import EntityExtractionService

__all__ = ["Criticality", "EntityExtractionService", "TechnicalEntityExtraction"]

