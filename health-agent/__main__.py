#!/usr/bin/env python3
"""
Main entry point for health_agent module.

Usage:
    python -m health-agent         # Start web UI
    python -m health-agent --cli   # Interactive CLI mode
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Health Agent - KI-gestützte Ernährungsplanung'
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode instead of web UI'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=7861,
        help='Web UI port (default: 7861)'
    )

    parser.add_argument(
        '--model', '-m',
        default='gemma3:4b',
        help='Ollama model name'
    )

    args = parser.parse_args()

    if args.cli:
        # CLI mode
        from .orchestrator import HealthOrchestrator
        from .api_client import get_client

        print("\n" + "=" * 50)
        print("HEALTH AGENT - Interactive Mode")
        print("=" * 50)
        print(f"\nModel: {args.model}")
        print("\nBefehle:")
        print("  /plan    - Wochenplan erstellen")
        print("  /recipe  - Rezept erstellen")
        print("  /search  - Produkte suchen")
        print("  /analyze - Nährwerte analysieren")
        print("  /quit    - Beenden")
        print()

        orchestrator = HealthOrchestrator(model_name=args.model)
        client = get_client()

        while True:
            try:
                user_input = input("health> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue

            if user_input in ['/quit', '/exit', '/q']:
                print("Bye!")
                break

            elif user_input.startswith('/plan'):
                print("\nErstelle Wochenplan...")
                result = orchestrator.create_week_plan()
                print(result.content if result.success else f"Fehler: {result.errors}")

            elif user_input.startswith('/recipe'):
                parts = user_input.split(maxsplit=1)
                dish = parts[1] if len(parts) > 1 else ""
                print(f"\nErstelle Rezept{f' für {dish}' if dish else ''}...")
                result = orchestrator.create_recipe(dish_name=dish)
                print(result.content if result.success else f"Fehler: {result.errors}")

            elif user_input.startswith('/search'):
                parts = user_input.split(maxsplit=1)
                query = parts[1] if len(parts) > 1 else ""
                if not query:
                    print("Verwendung: /search <suchbegriff>")
                    continue
                products = client.search(query)
                print(f"\nGefunden: {len(products)} Produkte")
                for p in products[:10]:
                    print(f"  - {p.name} ({p.store}) - {p.nutrition_summary()}")

            elif user_input.startswith('/analyze'):
                parts = user_input.split(maxsplit=1)
                meal = parts[1] if len(parts) > 1 else ""
                if not meal:
                    print("Verwendung: /analyze <mahlzeit beschreibung>")
                    continue
                print("\nAnalysiere...")
                result = orchestrator.analyze_nutrition(meal)
                print(result.content if result.success else f"Fehler: {result.errors}")

            else:
                print("Unbekannter Befehl. Nutze /plan, /recipe, /search, /analyze oder /quit")

            print()

    else:
        # Web UI mode
        from .app import create_ui
        app = create_ui()
        app.launch(
            server_name="0.0.0.0",
            server_port=args.port,
            share=False,
            show_error=True
        )


if __name__ == "__main__":
    main()
