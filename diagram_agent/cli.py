#!/usr/bin/env python3
"""
Diagram Agent CLI

Command-line interface for the diagram generation agent system.
"""

import argparse
import sys
import json
from pathlib import Path

from .orchestrator import DiagramOrchestrator, create_diagram, quick_diagram, PipelineResult
from .tools import validate_diagram, render_diagram, DiagramFormat


def main():
    parser = argparse.ArgumentParser(
        description='Diagram Agent - Multi-agent diagram generation with Google ADK + Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate a diagram from description
  python -m diagram_agent "A pipeline: Input -> Process -> Output"

  # Specify format and model
  python -m diagram_agent "User login flow" --format mermaid --model qwen2.5-coder:7b

  # Quick mode (faster, simpler)
  python -m diagram_agent "Database schema" --quick

  # Validate existing code
  python -m diagram_agent --validate code.dot

  # Interactive mode
  python -m diagram_agent --interactive
'''
    )

    parser.add_argument(
        'description',
        nargs='?',
        help='Text description of the diagram to generate'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['graphviz', 'mermaid', 'plantuml'],
        default='graphviz',
        help='Diagram format (default: graphviz)'
    )

    parser.add_argument(
        '--model', '-m',
        default='gemma3:4b',
        help='Ollama model name (default: gemma3:4b)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output PNG filename'
    )

    parser.add_argument(
        '--output-dir', '-d',
        default='./diagram_output',
        help='Output directory (default: ./diagram_output)'
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Quick mode - skip analysis, single pass'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Max improvement iterations (default: 3)'
    )

    parser.add_argument(
        '--validate',
        metavar='FILE',
        help='Validate an existing diagram file'
    )

    parser.add_argument(
        '--render',
        metavar='FILE',
        help='Render an existing diagram file to PNG'
    )

    parser.add_argument(
        '--code-only',
        action='store_true',
        help='Output only the diagram code, no PNG'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available Ollama models'
    )

    args = parser.parse_args()

    # Handle special modes
    if args.list_models:
        list_ollama_models()
        return

    if args.validate:
        validate_file(args.validate, args.json)
        return

    if args.render:
        render_file(args.render, args.output, args.output_dir, args.json)
        return

    if args.interactive:
        interactive_mode(args)
        return

    # Regular diagram generation
    if not args.description:
        parser.print_help()
        print("\nError: Please provide a diagram description or use --interactive mode")
        sys.exit(1)

    generate_diagram(args)


def generate_diagram(args):
    """Generate a diagram from the command line arguments."""

    if args.quick:
        # Quick mode - simple generation
        print(f"Generating {args.format} diagram (quick mode)...")
        code = quick_diagram(args.description, args.format)

        if args.code_only:
            print(code)
            return

        # Validate and render
        validation = validate_diagram(code, args.format)

        if validation.valid:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            filename = args.output or f"diagram_{datetime.now().strftime('%H%M%S')}.png"
            output_path = str(output_dir / filename)

            result = render_diagram(code, output_path, DiagramFormat(args.format))

            if result.success:
                print(f"✓ Saved: {result.output_path}")
                if args.json:
                    print(json.dumps({"success": True, "path": result.output_path, "code": code}))
            else:
                print(f"✗ Render failed: {result.error}")
        else:
            print(f"✗ Invalid code: {validation.errors}")
            print("\nGenerated code:")
            print(code)

    else:
        # Full pipeline mode
        orchestrator = DiagramOrchestrator(
            model_name=args.model,
            output_dir=args.output_dir,
            max_improvement_iterations=args.max_iterations,
            preferred_format=args.format
        )

        result = orchestrator.run(args.description, args.output)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print_result(result)


def print_result(result: PipelineResult):
    """Pretty print a pipeline result."""
    print("\n" + "=" * 50)
    print("DIAGRAM GENERATION RESULT")
    print("=" * 50)

    status = "✓ SUCCESS" if result.success else "✗ FAILED"
    print(f"\nStatus: {status}")

    if result.format:
        print(f"Format: {result.format.value}")

    print(f"Iterations: {result.iterations}")
    print(f"Duration: {result.duration_seconds:.2f}s")

    if result.output_path:
        print(f"\nOutput: {result.output_path}")

    if result.errors:
        print("\nErrors:")
        for err in result.errors:
            print(f"  - {err}")

    if result.diagram_code:
        print("\nGenerated Code:")
        print("-" * 40)
        # Truncate long code
        code = result.diagram_code
        if len(code) > 1000:
            code = code[:1000] + "\n... (truncated)"
        print(code)

    print()


def validate_file(filepath: str, as_json: bool = False):
    """Validate an existing diagram file."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    result = validate_diagram(code)

    if as_json:
        print(json.dumps({
            "valid": result.valid,
            "format": result.format.value,
            "errors": result.errors,
            "suggestions": result.suggestions
        }, indent=2))
    else:
        if result.valid:
            print(f"✓ Valid {result.format.value} code")
        else:
            print(f"✗ Invalid {result.format.value} code")
            print("\nErrors:")
            for err in result.errors:
                print(f"  - {err}")
            if result.suggestions:
                print("\nSuggestions:")
                for sug in result.suggestions:
                    print(f"  - {sug}")


def render_file(filepath: str, output: str = None, output_dir: str = "./diagram_output", as_json: bool = False):
    """Render an existing diagram file to PNG."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Determine output path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if output:
        output_file = str(output_path / output)
    else:
        output_file = str(output_path / (Path(filepath).stem + ".png"))

    result = render_diagram(code, output_file)

    if as_json:
        print(json.dumps({
            "success": result.success,
            "output_path": result.output_path,
            "error": result.error,
            "format": result.format.value
        }, indent=2))
    else:
        if result.success:
            print(f"✓ Rendered: {result.output_path}")
        else:
            print(f"✗ Render failed: {result.error}")


def list_ollama_models():
    """List available Ollama models."""
    try:
        import ollama
        models = ollama.list()

        print("\nAvailable Ollama Models:")
        print("-" * 40)

        for model in models.get('models', []):
            name = model.get('name', 'unknown')
            size = model.get('size', 0) / (1024**3)
            print(f"  {name} ({size:.1f} GB)")

        print()

    except ImportError:
        print("Error: ollama package not installed")
        print("Install with: pip install ollama")
    except Exception as e:
        print(f"Error listing models: {e}")


def interactive_mode(args):
    """Run in interactive mode."""
    print("\n" + "=" * 50)
    print("DIAGRAM AGENT - Interactive Mode")
    print("=" * 50)
    print(f"\nModel: {args.model}")
    print(f"Format: {args.format}")
    print("\nCommands:")
    print("  /format <graphviz|mermaid|plantuml> - Change format")
    print("  /model <name> - Change model")
    print("  /quick - Toggle quick mode")
    print("  /help - Show help")
    print("  /quit - Exit")
    print("\nOr just type a diagram description to generate.\n")

    quick_mode = args.quick
    current_format = args.format
    current_model = args.model

    while True:
        try:
            user_input = input("diagram> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.startswith('/'):
            cmd = user_input.split()
            command = cmd[0].lower()

            if command == '/quit' or command == '/exit':
                print("Bye!")
                break

            elif command == '/format' and len(cmd) > 1:
                fmt = cmd[1].lower()
                if fmt in ['graphviz', 'mermaid', 'plantuml']:
                    current_format = fmt
                    print(f"Format set to: {current_format}")
                else:
                    print("Invalid format. Use: graphviz, mermaid, or plantuml")

            elif command == '/model' and len(cmd) > 1:
                current_model = cmd[1]
                print(f"Model set to: {current_model}")

            elif command == '/quick':
                quick_mode = not quick_mode
                print(f"Quick mode: {'ON' if quick_mode else 'OFF'}")

            elif command == '/help':
                print("\nCommands:")
                print("  /format <graphviz|mermaid|plantuml>")
                print("  /model <ollama-model-name>")
                print("  /quick - Toggle quick mode")
                print("  /quit - Exit")

            else:
                print(f"Unknown command: {command}")

        else:
            # Generate diagram
            print(f"\nGenerating {current_format} diagram...")

            if quick_mode:
                code = quick_diagram(user_input, current_format)
                validation = validate_diagram(code, current_format)

                if validation.valid:
                    print("\n✓ Valid code generated:")
                    print("-" * 40)
                    print(code)
                else:
                    print("\n⚠ Code has issues:")
                    for err in validation.errors:
                        print(f"  - {err}")
                    print("\nGenerated code:")
                    print(code)
            else:
                orchestrator = DiagramOrchestrator(
                    model_name=current_model,
                    output_dir=args.output_dir,
                    preferred_format=current_format
                )
                result = orchestrator.run(user_input)
                print_result(result)

            print()


if __name__ == "__main__":
    main()
