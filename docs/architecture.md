# Arquitectura

```mermaid
flowchart LR
    CLI[CLI asíncrona] --> Manager[Gestor LLM]
    Manager --> OpenAI[OpenAI]
    Manager --> Anthropic[Anthropic]

    Input[Texto técnico] --> Prompt[ChatPromptTemplate]
    Prompt --> Structured[Modelo con salida Pydantic]
    Structured --> Extraction[Entidades técnicas]

    Files[Archivos TXT y MD] --> Chunks[Chunks de 500 tokens]
    Chunks --> Embeddings[Embeddings]
    Embeddings --> Chroma[(Chroma local)]
    Question[Pregunta] --> Chroma
    Chroma --> Context[Top-k fragmentos]
    Context --> Answer[Respuesta estructurada]
    Answer --> Sources[Referencias y evidencias]
```

## Límites de los componentes

- `llm`: contrato común, selección de proveedor, reintentos y streaming.
- `extraction`: prompt, esquema de entidades y ejecución LCEL asíncrona.
- `rag`: carga, fragmentación, persistencia, recuperación y respuesta respaldada.
- `integrations`: construcción de modelos y embeddings de terceros.
- `cli`: interfaces ejecutables para operación y demostración.

Las dependencias externas quedan detrás de adaptadores. Los servicios aceptan implementaciones
inyectadas, lo que permite verificar la lógica sin red ni credenciales.
