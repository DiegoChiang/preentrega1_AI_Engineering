# Cliente LLM robusto y asíncrono

Cliente unificado en Python 3.12 para trabajar con OpenAI y Anthropic mediante una interfaz común.
Admite generación completa, streaming asíncrono, validación con Pydantic y reintentos ante fallos
transitorios.

## Capacidades

- Selección de OpenAI o Anthropic mediante `AsyncLLMManager`.
- SDK oficiales `AsyncOpenAI` y `AsyncAnthropic`.
- Métodos no bloqueantes basados en `async` y `await`.
- Streaming mediante un generador `AsyncIterator[str]`.
- Mensajes, configuración y respuestas validados con Pydantic.
- Temperatura restringida al rango de 0 a 2.
- Reintentos con backoff exponencial para red, cuota y rate limiting.
- Errores controlados de configuración y proveedor.

## Instalación

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Completar las variables necesarias:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
ANTHROPIC_MODEL=claude-sonnet-4-6
```

`.env` está excluido del control de versiones.

## Ejecución

Generación completa:

```bash
python main.py "¿Qué es la entropía?" --provider openai
```

Streaming:

```bash
python main.py "¿Qué es la entropía?" --provider anthropic --stream
```

Generación completa y streaming:

```bash
python main.py "¿Qué es la entropía?" --provider openai --both
```

## Contratos principales

- `ChatMessage`: rol y contenido del mensaje.
- `ModelConfig`: proveedor, modelo, temperatura, límite de tokens, timeout y reintentos.
- `ModelResponse`: contenido, proveedor, modelo, motivo de finalización y uso de tokens.
- `BaseLLMClient`: interfaz común con `generate()` y `stream()`.

## Verificación

```bash
pytest
ruff check .
python -m compileall src main.py
```

Las pruebas usan dobles de los SDK y no consumen créditos.

## Estructura

```text
.
├── docs/llm_client.md
├── src/incident_intelligence/
│   ├── cli/llm_demo.py
│   ├── llm/
│   │   ├── base.py
│   │   ├── manager.py
│   │   ├── openai_client.py
│   │   └── anthropic_client.py
│   ├── config.py
│   ├── errors.py
│   ├── retry.py
│   └── schemas.py
├── tests/
├── .env.example
├── main.py
└── pyproject.toml
```
