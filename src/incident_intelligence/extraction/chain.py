"""Cadena LCEL para extraer entidades técnicas."""

from typing import Any

from incident_intelligence.config import Settings
from incident_intelligence.extraction.schemas import TechnicalEntityExtraction
from incident_intelligence.integrations.langchain import build_chat_model

SYSTEM_PROMPT = """Eres un analista de incidentes de software.
Extrae únicamente información respaldada por el texto recibido.
Identifica tecnologías concretas, asigna criticidad baja, media o alta y redacta un resumen
técnico breve. La criticidad alta corresponde a indisponibilidad, pérdida de datos, acceso no
autorizado o impacto generalizado; media a degradación parcial; baja a consultas o problemas
sin impacto operativo. No inventes tecnologías ausentes."""


def build_extraction_chain(settings: Settings) -> Any:
    """Compone prompt, modelo estructurado y política de reintentos."""

    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError("Instala la dependencia 'langchain-core'") from exc

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Texto técnico:\n{text}"),
        ]
    )
    model = build_chat_model(settings)
    structured_model = model.with_structured_output(TechnicalEntityExtraction)
    chain = prompt | structured_model
    return chain.with_retry(
        retry_if_exception_type=(Exception,),
        wait_exponential_jitter=True,
        stop_after_attempt=settings.llm_max_retries,
    )

