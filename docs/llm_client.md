# Cliente LLM asíncrono

## Objetivo

El cliente ofrece una interfaz común para OpenAI y Anthropic. La selección del proveedor depende de
la configuración, mientras que el código consumidor utiliza los mismos contratos de mensajes,
generación completa y streaming.

## Componentes

| Componente | Responsabilidad |
| --- | --- |
| `schemas.py` | Valida mensajes, proveedor, modelo, parámetros de generación, respuesta y uso de tokens. |
| `llm/base.py` | Define las operaciones asíncronas `generate` y `stream`. |
| `llm/openai_client.py` | Adapta el SDK asíncrono de OpenAI a la interfaz común. |
| `llm/anthropic_client.py` | Adapta el SDK asíncrono de Anthropic a la interfaz común. |
| `llm/manager.py` | Selecciona el adaptador y construye su configuración. |
| `retry.py` | Ejecuta reintentos asíncronos con backoff exponencial y jitter. |
| `errors.py` | Diferencia errores de configuración y fallos de proveedor. |
| `cli/llm_demo.py` | Ejecuta consultas completas, streaming o ambos modos. |

## Flujo de una consulta

1. `Settings` carga el proveedor, los modelos, los límites y las claves desde variables de entorno.
2. `AsyncLLMManager` valida el proveedor y la presencia de su clave.
3. `ModelConfig` valida temperatura, tokens, timeout, reintentos y nombre del modelo.
4. El adaptador convierte `ChatMessage` al formato requerido por el SDK.
5. `generate` devuelve un `ModelResponse` con contenido, modelo, motivo de finalización y tokens.
6. `stream` entrega fragmentos mediante un iterador asíncrono.

## Configuración

Crear el entorno e instalar las dependencias:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Variables principales:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
ANTHROPIC_MODEL=claude-sonnet-4-6
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1200
LLM_TIMEOUT_SECONDS=45
LLM_MAX_RETRIES=3
```

Las claves permanecen en `.env`; el repositorio solo incluye `.env.example` sin secretos.

## Ejecución

Consulta completa con OpenAI:

```powershell
python main.py llm "¿Qué es entropía?" --provider openai
```

Streaming con Anthropic:

```powershell
python main.py llm "¿Qué es entropía?" --provider anthropic --stream
```

Ambos modos con el mismo proveedor:

```powershell
python main.py llm "¿Qué es entropía?" --provider openai --both
```

También están disponibles los comandos equivalentes mediante `llm-demo` después de instalar el
proyecto.

## Comportamiento ante fallos

- La ausencia de una clave produce `LLMConfigurationError` antes de enviar una solicitud.
- Los proveedores no admitidos producen `LLMConfigurationError`.
- Los fallos de red, cuota o servicio se convierten en `LLMProviderError`.
- La generación completa aplica reintentos con backoff exponencial y jitter.
- El streaming solo reintenta antes del primer fragmento para evitar texto duplicado.
- `asyncio.CancelledError` se propaga para conservar la cancelación de tareas.
- Los SDK tienen sus reintentos internos desactivados para evitar ciclos duplicados.

## Verificación

Las pruebas unitarias usan dobles asíncronos y no consumen créditos:

```powershell
pytest tests/test_schemas.py tests/test_retry.py tests/test_llm_manager.py tests/test_llm_clients.py
ruff check src tests main.py
python -m compileall src main.py
```

Cobertura funcional:

- validación de mensajes y parámetros;
- selección de OpenAI y Anthropic;
- respuesta normal y conteo de tokens;
- streaming incremental de ambos proveedores;
- separación del mensaje de sistema para Anthropic;
- reintentos de fallos transitorios;
- propagación de cancelaciones;
- errores controlados por proveedor y configuración.
