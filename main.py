"""Punto de entrada para los tres flujos del proyecto."""

import argparse

from incident_intelligence.cli import extract_entities, llm_demo, rag_local


def main() -> None:
    parser = argparse.ArgumentParser(description="Plataforma de inteligencia de incidentes")
    parser.add_argument("component", choices=("llm", "extract", "rag"))
    args, remaining = parser.parse_known_args()

    import sys

    sys.argv = [sys.argv[0], *remaining]
    commands = {
        "llm": llm_demo.main,
        "extract": extract_entities.main,
        "rag": rag_local.main,
    }
    commands[args.component]()


if __name__ == "__main__":
    main()
