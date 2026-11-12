"""Demostración del cliente asíncrono multiproveedor."""

import argparse
import asyncio
import json

from incident_intelligence.config import Settings
from incident_intelligence.llm.manager import AsyncLLMManager
from incident_intelligence.schemas import ChatMessage, MessageRole, Provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consulta OpenAI o Anthropic de forma asíncrona")
    parser.add_argument("question", help="Pregunta enviada al modelo")
    parser.add_argument("--provider", choices=[item.value for item in Provider])
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--stream", action="store_true", help="Imprime tokens a medida que llegan")
    output.add_argument(
        "--both",
        action="store_true",
        help="Ejecuta generación completa y streaming en la misma consulta",
    )
    return parser


async def run(question: str, provider: str | None, stream: bool) -> None:
    settings = Settings()
    client = AsyncLLMManager(settings).create(provider)
    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="Responde en español con precisión y sin inventar información.",
        ),
        ChatMessage(role=MessageRole.USER, content=question),
    ]

    if stream:
        async for token in client.stream(messages):
            print(token, end="", flush=True)
        print()
        return

    response = await client.generate(messages)
    print(json.dumps(response.model_dump(mode="json"), ensure_ascii=False, indent=2))


async def run_both(question: str, provider: str | None) -> None:
    print("Respuesta completa:")
    await run(question, provider, stream=False)
    print("\nStreaming:")
    await run(question, provider, stream=True)


def main() -> None:
    args = build_parser().parse_args()
    if args.both:
        asyncio.run(run_both(args.question, args.provider))
        return
    asyncio.run(run(args.question, args.provider, args.stream))


if __name__ == "__main__":
    main()
