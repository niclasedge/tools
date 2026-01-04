#!/usr/bin/env python3
"""
Graphviz Visualization Tool

Dieses Tool analysiert Input-Daten, erstellt DOT-Graphviz-Dokumente und rendert sie als PNG.
Es kann auch Ollama-Modelle testen, um zu prüfen, welches validen Graphviz-Code generiert.
"""

import subprocess
import tempfile
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ValidationResult(Enum):
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class GraphvizResult:
    """Ergebnis einer Graphviz-Operation"""
    success: bool
    message: str
    dot_code: Optional[str] = None
    output_path: Optional[str] = None
    validation_result: ValidationResult = ValidationResult.ERROR
    errors: Optional[List[str]] = None


def check_graphviz_installed() -> bool:
    """Prüft, ob Graphviz (dot) installiert ist."""
    try:
        result = subprocess.run(
            ["dot", "-V"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def validate_dot_code(dot_code: str) -> Tuple[bool, List[str]]:
    """
    Validiert DOT-Code ohne ihn zu rendern.

    Args:
        dot_code: Der zu validierende DOT-Code

    Returns:
        Tuple aus (ist_valid, liste_von_fehlern)
    """
    errors = []

    # Grundlegende Syntaxprüfungen
    dot_code_stripped = dot_code.strip()

    # Prüfe ob Graph-Definition vorhanden
    if not any(keyword in dot_code_stripped.lower() for keyword in ['digraph', 'graph', 'subgraph']):
        errors.append("Keine gültige Graph-Definition gefunden (digraph/graph/subgraph)")

    # Prüfe Klammern-Balance
    open_braces = dot_code.count('{')
    close_braces = dot_code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalancierte geschweifte Klammern: {open_braces} '{{' vs {close_braces} '}}'")

    # Verwende dot -Tcanon für tiefere Validierung
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            temp_path = f.name

        result = subprocess.run(
            ["dot", "-Tcanon", temp_path],
            capture_output=True,
            text=True
        )

        os.unlink(temp_path)

        if result.returncode != 0:
            # Parse Fehlermeldungen
            error_lines = result.stderr.strip().split('\n')
            for line in error_lines:
                if line.strip():
                    errors.append(line.strip())
            return False, errors

        return True, []

    except Exception as e:
        errors.append(f"Validierungsfehler: {str(e)}")
        return False, errors


def render_dot_to_png(dot_code: str, output_path: str, validate_first: bool = True) -> GraphvizResult:
    """
    Rendert DOT-Code als PNG.

    Args:
        dot_code: Der zu rendernde DOT-Code
        output_path: Pfad für die Ausgabe-PNG
        validate_first: Ob der Code vor dem Rendern validiert werden soll

    Returns:
        GraphvizResult mit Ergebnisinformationen
    """
    if not check_graphviz_installed():
        return GraphvizResult(
            success=False,
            message="Graphviz ist nicht installiert. Bitte installieren mit: apt-get install graphviz",
            validation_result=ValidationResult.ERROR
        )

    # Optionale Validierung
    if validate_first:
        is_valid, errors = validate_dot_code(dot_code)
        if not is_valid:
            return GraphvizResult(
                success=False,
                message="DOT-Code ist ungültig",
                dot_code=dot_code,
                validation_result=ValidationResult.INVALID,
                errors=errors
            )

    # Rendern
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            temp_dot_path = f.name

        # Stelle sicher, dass output_path ein absoluter Pfad ist
        output_path = os.path.abspath(output_path)

        result = subprocess.run(
            ["dot", "-Tpng", temp_dot_path, "-o", output_path],
            capture_output=True,
            text=True
        )

        os.unlink(temp_dot_path)

        if result.returncode != 0:
            return GraphvizResult(
                success=False,
                message=f"Rendering fehlgeschlagen: {result.stderr}",
                dot_code=dot_code,
                validation_result=ValidationResult.INVALID,
                errors=[result.stderr]
            )

        return GraphvizResult(
            success=True,
            message=f"PNG erfolgreich erstellt: {output_path}",
            dot_code=dot_code,
            output_path=output_path,
            validation_result=ValidationResult.VALID
        )

    except Exception as e:
        return GraphvizResult(
            success=False,
            message=f"Fehler beim Rendern: {str(e)}",
            dot_code=dot_code,
            validation_result=ValidationResult.ERROR,
            errors=[str(e)]
        )


def save_dot_file(dot_code: str, output_path: str) -> GraphvizResult:
    """
    Speichert DOT-Code in eine Datei.

    Args:
        dot_code: Der DOT-Code
        output_path: Pfad für die .dot-Datei

    Returns:
        GraphvizResult
    """
    try:
        output_path = os.path.abspath(output_path)
        with open(output_path, 'w') as f:
            f.write(dot_code)
        return GraphvizResult(
            success=True,
            message=f"DOT-Datei gespeichert: {output_path}",
            dot_code=dot_code,
            output_path=output_path,
            validation_result=ValidationResult.VALID
        )
    except Exception as e:
        return GraphvizResult(
            success=False,
            message=f"Fehler beim Speichern: {str(e)}",
            dot_code=dot_code,
            validation_result=ValidationResult.ERROR,
            errors=[str(e)]
        )


# ============== Ollama Model Testing ==============

def test_ollama_model(model_name: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
    """
    Testet ein Ollama-Modell auf seine Fähigkeit, validen Graphviz-Code zu generieren.

    Args:
        model_name: Name des Ollama-Modells
        prompt: Der Prompt für das Modell
        timeout: Timeout in Sekunden

    Returns:
        Dict mit Testergebnissen
    """
    try:
        import ollama
    except ImportError:
        return {
            "model": model_name,
            "success": False,
            "error": "Ollama Python-Paket nicht installiert. Installieren mit: pip install ollama",
            "valid_graphviz": False
        }

    result = {
        "model": model_name,
        "prompt": prompt,
        "success": False,
        "response": None,
        "extracted_dot_code": None,
        "valid_graphviz": False,
        "validation_errors": [],
        "error": None
    }

    try:
        # Generiere Antwort vom Modell
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            options={"timeout": timeout}
        )

        result["success"] = True
        result["response"] = response.get("response", "")

        # Extrahiere DOT-Code aus der Antwort
        dot_code = extract_dot_code(result["response"])
        result["extracted_dot_code"] = dot_code

        if dot_code:
            # Validiere den extrahierten Code
            is_valid, errors = validate_dot_code(dot_code)
            result["valid_graphviz"] = is_valid
            result["validation_errors"] = errors
        else:
            result["validation_errors"] = ["Kein DOT-Code in der Antwort gefunden"]

    except Exception as e:
        result["error"] = str(e)

    return result


def extract_dot_code(text: str) -> Optional[str]:
    """
    Extrahiert DOT-Code aus einem Text (z.B. aus Markdown-Codeblöcken).

    Args:
        text: Der Text, der DOT-Code enthalten könnte

    Returns:
        Der extrahierte DOT-Code oder None
    """
    import re

    # Versuche Code aus Markdown-Codeblöcken zu extrahieren
    # Pattern für ```dot ... ``` oder ```graphviz ... ``` oder ``` ... ```
    patterns = [
        r'```(?:dot|graphviz)\s*\n(.*?)\n```',
        r'```\s*\n((?:di)?graph\s+\w+\s*\{.*?\})\s*\n```',
        r'((?:di)?graph\s+\w+\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\})',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            # Nimm den ersten passenden Match
            code = matches[0].strip()
            if code:
                return code

    # Fallback: Suche nach digraph/graph Blöcken
    if 'digraph' in text.lower() or 'graph' in text.lower():
        # Versuche den gesamten Graph-Block zu extrahieren
        match = re.search(
            r'((?:di)?graph\s+\w+\s*\{[\s\S]*?\})\s*(?:```|$)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

    return None


def test_multiple_models(
    models: List[str],
    prompt: str,
    output_dir: str = "./model_tests"
) -> List[Dict[str, Any]]:
    """
    Testet mehrere Ollama-Modelle und vergleicht ihre Graphviz-Fähigkeiten.

    Args:
        models: Liste von Modellnamen
        prompt: Der Prompt für alle Modelle
        output_dir: Verzeichnis für Ausgabedateien

    Returns:
        Liste mit Testergebnissen für jedes Modell
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for model in models:
        print(f"\nTeste Modell: {model}...")
        result = test_ollama_model(model, prompt)
        results.append(result)

        # Wenn valider DOT-Code generiert wurde, erstelle PNG
        if result["valid_graphviz"] and result["extracted_dot_code"]:
            safe_model_name = model.replace(":", "_").replace("/", "_")
            png_path = os.path.join(output_dir, f"{safe_model_name}_output.png")
            dot_path = os.path.join(output_dir, f"{safe_model_name}_output.dot")

            # Speichere DOT-Datei
            save_dot_file(result["extracted_dot_code"], dot_path)

            # Erstelle PNG
            render_result = render_dot_to_png(
                result["extracted_dot_code"],
                png_path,
                validate_first=False  # Bereits validiert
            )
            result["png_path"] = png_path if render_result.success else None
            result["dot_path"] = dot_path

        # Status ausgeben
        status = "✓ VALID" if result["valid_graphviz"] else "✗ INVALID"
        print(f"  {status}")
        if result["validation_errors"]:
            for err in result["validation_errors"][:3]:  # Max 3 Fehler zeigen
                print(f"    - {err}")

    return results


def print_model_comparison(results: List[Dict[str, Any]]) -> None:
    """Gibt eine Vergleichstabelle der Modell-Ergebnisse aus."""
    print("\n" + "=" * 60)
    print("MODELL-VERGLEICH: Graphviz-Code-Generierung")
    print("=" * 60)

    valid_count = sum(1 for r in results if r["valid_graphviz"])
    total_count = len(results)

    print(f"\nErgebnis: {valid_count}/{total_count} Modelle generierten validen Code\n")

    for r in results:
        status = "✓" if r["valid_graphviz"] else "✗"
        model = r["model"]
        print(f"  {status} {model}")

        if r.get("error"):
            print(f"      Fehler: {r['error']}")
        elif not r["valid_graphviz"] and r["validation_errors"]:
            print(f"      Validierungsfehler: {r['validation_errors'][0]}")
        elif r.get("png_path"):
            print(f"      PNG: {r['png_path']}")

    print()


# ============== Beispiel-Graphen ==============

def create_example_graph() -> str:
    """Erstellt einen Beispiel-Graphen."""
    return '''digraph Example {
    rankdir=LR;
    node [shape=box, style=filled, fillcolor=lightblue];

    Start -> Process1;
    Start -> Process2;
    Process1 -> End;
    Process2 -> End;

    Start [fillcolor=green];
    End [fillcolor=red];
}'''


def create_flowchart(steps: List[str], title: str = "Flowchart") -> str:
    """
    Erstellt einen einfachen Flowchart aus einer Liste von Schritten.

    Args:
        steps: Liste von Schritt-Beschreibungen
        title: Titel des Graphen

    Returns:
        DOT-Code
    """
    safe_title = title.replace(" ", "_").replace("-", "_")
    dot_lines = [
        f'digraph {safe_title} {{',
        '    rankdir=TB;',
        '    node [shape=box, style="rounded,filled", fillcolor=lightblue];',
        ''
    ]

    for i, step in enumerate(steps):
        node_name = f"step{i}"
        # Escape Anführungszeichen im Label
        safe_label = step.replace('"', '\\"')
        dot_lines.append(f'    {node_name} [label="{safe_label}"];')

    dot_lines.append('')

    # Verbindungen
    for i in range(len(steps) - 1):
        dot_lines.append(f'    step{i} -> step{i+1};')

    dot_lines.append('}')

    return '\n'.join(dot_lines)


def create_hierarchy(data: Dict[str, Any], title: str = "Hierarchy") -> str:
    """
    Erstellt einen Hierarchie-Graphen aus verschachtelten Daten.

    Args:
        data: Verschachtelte Daten (Dict mit Listen/Dicts als Werte)
        title: Titel des Graphen

    Returns:
        DOT-Code
    """
    safe_title = title.replace(" ", "_").replace("-", "_")
    dot_lines = [
        f'digraph {safe_title} {{',
        '    rankdir=TB;',
        '    node [shape=box, style=filled, fillcolor=lightyellow];',
        ''
    ]

    node_counter = [0]

    def add_node(label: str) -> str:
        node_id = f"node{node_counter[0]}"
        node_counter[0] += 1
        safe_label = str(label).replace('"', '\\"')
        dot_lines.append(f'    {node_id} [label="{safe_label}"];')
        return node_id

    def process_dict(d: Dict, parent_id: Optional[str] = None):
        for key, value in d.items():
            node_id = add_node(key)
            if parent_id:
                dot_lines.append(f'    {parent_id} -> {node_id};')

            if isinstance(value, dict):
                process_dict(value, node_id)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        process_dict(item, node_id)
                    else:
                        child_id = add_node(item)
                        dot_lines.append(f'    {node_id} -> {child_id};')

    process_dict(data)
    dot_lines.append('}')

    return '\n'.join(dot_lines)


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(
        description='Graphviz Visualization Tool - Erstellt und validiert DOT-Graphen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Beispiele:
  # Validiere eine DOT-Datei
  python graphviz_tool.py validate input.dot

  # Rendere DOT zu PNG
  python graphviz_tool.py render input.dot output.png

  # Erstelle Beispiel-Graph
  python graphviz_tool.py example --output example.png

  # Teste Ollama-Modelle
  python graphviz_tool.py test-models llama2 mistral codellama --prompt "Create a flowchart for login process"
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validiere DOT-Code')
    validate_parser.add_argument('input', help='DOT-Datei oder - für stdin')

    # Render command
    render_parser = subparsers.add_parser('render', help='Rendere DOT zu PNG')
    render_parser.add_argument('input', help='DOT-Datei oder - für stdin')
    render_parser.add_argument('output', help='Ausgabe-PNG-Datei')
    render_parser.add_argument('--no-validate', action='store_true', help='Überspringe Validierung')

    # Example command
    example_parser = subparsers.add_parser('example', help='Erstelle Beispiel-Graph')
    example_parser.add_argument('--output', '-o', default='example.png', help='Ausgabe-PNG-Datei')
    example_parser.add_argument('--dot-output', help='Speichere auch DOT-Datei')

    # Test models command
    test_parser = subparsers.add_parser('test-models', help='Teste Ollama-Modelle')
    test_parser.add_argument('models', nargs='+', help='Zu testende Modelle')
    test_parser.add_argument('--prompt', '-p', required=True, help='Prompt für die Modelle')
    test_parser.add_argument('--output-dir', '-o', default='./model_tests', help='Ausgabeverzeichnis')

    # Flowchart command
    flow_parser = subparsers.add_parser('flowchart', help='Erstelle Flowchart aus Schritten')
    flow_parser.add_argument('steps', nargs='+', help='Schritte für den Flowchart')
    flow_parser.add_argument('--output', '-o', default='flowchart.png', help='Ausgabe-PNG-Datei')
    flow_parser.add_argument('--title', '-t', default='Flowchart', help='Titel des Graphen')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'validate':
        if args.input == '-':
            dot_code = sys.stdin.read()
        else:
            with open(args.input, 'r') as f:
                dot_code = f.read()

        is_valid, errors = validate_dot_code(dot_code)

        if is_valid:
            print("✓ DOT-Code ist valide")
            sys.exit(0)
        else:
            print("✗ DOT-Code ist ungültig:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)

    elif args.command == 'render':
        if args.input == '-':
            dot_code = sys.stdin.read()
        else:
            with open(args.input, 'r') as f:
                dot_code = f.read()

        result = render_dot_to_png(
            dot_code,
            args.output,
            validate_first=not args.no_validate
        )

        print(result.message)
        if not result.success and result.errors:
            for err in result.errors:
                print(f"  - {err}")

        sys.exit(0 if result.success else 1)

    elif args.command == 'example':
        dot_code = create_example_graph()

        if args.dot_output:
            save_dot_file(dot_code, args.dot_output)
            print(f"DOT-Datei gespeichert: {args.dot_output}")

        result = render_dot_to_png(dot_code, args.output)
        print(result.message)
        sys.exit(0 if result.success else 1)

    elif args.command == 'test-models':
        results = test_multiple_models(args.models, args.prompt, args.output_dir)
        print_model_comparison(results)

        # Speichere Ergebnisse als JSON
        json_path = os.path.join(args.output_dir, "results.json")
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Ergebnisse gespeichert: {json_path}")

    elif args.command == 'flowchart':
        dot_code = create_flowchart(args.steps, args.title)
        result = render_dot_to_png(dot_code, args.output)
        print(result.message)

        # Zeige auch DOT-Code
        print("\nGenerierter DOT-Code:")
        print(dot_code)

        sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
