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
import re


# ============== Mindmap Prompt Template ==============

MINDMAP_PROMPT_TEMPLATE = '''<Prompt>
    <Role>Du bist ein Experte für Wissensvisualisierung und Mindmapping. Deine Aufgabe ist es, den unten folgenden Text zu analysieren und ihn in eine hochstrukturierte, optimierte und intuitive Level-3-Mindmap umzuwandeln.</Role>

    <Goal>Erstelle eine Mindmap, die tiefes Verständnis fördert, Schlüsselkonzepte hervorhebt, Beziehungen klar aufzeigt und leicht merkbar ist. Sie soll die Prinzipien einer Level-3-Mindmap verkörpern.</Goal>

    <OutputFormat>
        Gib **ausschließlich** Graphviz `digraph` Code im DOT-Format aus. Orientiere dich dabei am Stil und der Syntax des `<SimplifiedSyntaxExample>` unten.
    </OutputFormat>

    <CoreInstructions>
        <Instruction id="1" category="Hauptthema">
            <title>Hauptthema Identifizieren</title>
            <details>
                - Identifiziere das zentrale Thema des Textes.
                - Mache es zum visuellen Zentrum (z.B. `shape=doubleoctagon`, `penwidth=2`, eigene `fillcolor`).
            </details>
        </Instruction>

        <Instruction id="2" category="Struktur">
            <title>Kernkonzepte & Struktur</title>
            <details>
                - Extrahiere Hauptideen/Themen als Hauptknoten.
                - Organisiere Knoten hierarchisch und logisch.
                - Nutze `rankdir=LR` (oder `TB` falls passender).
            </details>
        </Instruction>

        <Instruction id="3" category="Gruppierung">
            <title>Gruppierung (Cluster)</title>
            <details>
                - Gruppiere thematisch verwandte Knoten klar mit `subgraph cluster_...`.
                - Gib Clustern aussagekräftige `label` und dezente `fillcolor`:
                  - Hellgelb/Orange für Basis/Gründe: `#FFF3CD`, `#FFEBCD`
                  - Hellblau für Ziele/Kompetenzen: `#DAE8FC`, `#EBF5FB`
                  - Hellgrün für Nutzen/Nachhaltigkeit: `#D5E8D4`, `#E8F5E9`
            </details>
        </Instruction>

        <Instruction id="4" category="Knoten-Styling">
            <title>Knoten-Styling</title>
            <details>
                - **Labels:** Extrem prägnante Schlüsselwörter/Phrasen (keine Sätze!).
                - **Umlaute:** Ersetze ä, ö, ü, ß **konsequent** durch ae, oe, ue, ss.
                - **Visuelle Kodierung:** Nutze `shape` (z.B. `ellipse`, `box`, `note`, `hexagon`, `diamond`) und `fillcolor` gezielt für Knotentypen oder Wichtigkeit.
                - **Betonung:** Wichtige Knoten mit `penwidth=1.5` oder `2`.
                - **Details:** Lange Erklärungen ins `tooltip`-Attribut.
            </details>
        </Instruction>

        <Instruction id="5" category="Verbindungen">
            <title>Verbindungen (Kanten)</title>
            <details>
                - Zeichne Kanten nur für klare Beziehungen.
                - **Beschriftung:** Verwende **`xlabel`** (wichtig: *nicht* `label`!) zur Beschreibung der Beziehung (z.B. `xlabel="fuehrt zu"`).
                - **Betonung:** Wichtige Kanten mit `penwidth=1.5` oder `2` und/oder `color` (z.B. `color=blue` für Hauptfortschritt, `color=darkgreen` für wichtigste Begründung).
                - **Stil:** Nutze `style=dashed`/`dotted` für sekundäre oder implizite Beziehungen.
                - **Richtung:** Setze `dir=forward`/`back` wenn die Richtung wesentlich ist.
            </details>
        </Instruction>

        <Instruction id="6" category="Qualitaet">
            <title>Qualität & Fokus</title>
            <details>
                - Ziel: Logische, klare, nicht überladene Struktur.
                - Fokus auf *Bedeutung* und *Zusammenhänge*, nicht nur Auflistung.
            </details>
        </Instruction>

        <Instruction id="7" category="Graphviz-Einstellungen">
            <title>Graphviz-Einstellungen</title>
            <details>
                - Verwende globale Einstellungen wie im `<SimplifiedSyntaxExample>` (z.B. `splines=ortho`, `nodesep`, `ranksep`, `fontsize`, `fontname`).
                - Definiere sinnvolle Default-Styles für `node` und `edge`. Diese dürfen *nicht* leer sein:
                    - node [style=filled, shape=box, fontname="Arial", fontsize=10];
                    - edge [fontname="Arial", fontsize=9, color=gray50];
                - wenn keine stile definiert werden sollen und die defaults genutzt werden, keine node ; oder edge ; angeben
            </details>
        </Instruction>

        <Instruction id="8" category="Konsistenz">
             <title>Konsistenz</title>
             <details>Halte dich stilistisch eng an das `<SimplifiedSyntaxExample>` (Farben, Formen, Betonung).</details>
        </Instruction>
    </CoreInstructions>

    <SimplifiedSyntaxExample>
        <title>Simplified Syntax Example (als Stil-Referenz)</title>
        <code>
digraph Gruende_Ziele_Ausbildung {{
    // Global Settings
    rankdir=LR;
    splines=ortho;
    nodesep=0.5; ranksep=1.0;
    overlap=false; pack=true; packmode="graph"; sep="+10,10";
    fontsize=12; fontname="Arial";

    // Default Styles (MUST contain styles)
    node [style=filled, shape=box, fontname="Arial", fontsize=10];
    edge [fontname="Arial", fontsize=9, color=gray50];

    // Central Topic
    Hauptthema [label="Gruende und Ziele
der Ausbildung", shape=doubleoctagon, penwidth=2, fillcolor="#D0E0F0", fontsize=14];

    // Cluster Example (Reasons/Base -> Yellow/Orange)
    subgraph cluster_Gruende {{
        label="Gruende fuer die Ausbildung"; fillcolor="#FFF3CD"; style=filled; penwidth=1; fontsize=11; fontname="Arial Bold";

        Wettbewerbsvorteil [label="Wettbewerbsvorteil", shape=hexagon, penwidth=2, fillcolor="#FFDAB9", tooltip="Wichtigster Grund..."];
        Nachwuchssicherung [label="Sicherung
Fachkraefte-Nachwuchs", shape=ellipse, fillcolor="#FFEBCD"];

        // Sub-Cluster Example
        subgraph cluster_OperativeKostengruende {{
            label = "Operative & Kostenvorteile"; fillcolor="#FFFFE0"; style=filled; fontsize=10;
            Identifikation [label="Identifikation
mit Betrieb", shape=note];
            KostenRekrutierung [label="Geringere
Rekrutierungskosten", shape=note, fillcolor="#F5CBA7"];
        }}
    }}

     // Cluster Example 2 (Goals/Competencies -> Blue)
    subgraph cluster_Ziele {{
        label="Ziele der Ausbildung"; fillcolor="#DAE8FC"; style=filled; penwidth=1; fontsize=11; fontname="Arial Bold";
        Handlungsfaehigkeit [label="Berufliche
Handlungsfaehigkeit", shape=diamond, penwidth=2, fillcolor="#A8C7FA", fontsize=12];

        subgraph cluster_Kompetenzen {{
             label="Kompetenzen"; fillcolor="#EBF5FB"; style=filled; fontsize=10;
             SozialKomp [label="Sozialkompetenz", shape=ellipse, fillcolor="#D6EAF8"];
             /* ... other competencies ... */
        }}
    }}

     // Cluster Example 3 (Benefits/Sustainability -> Green)
    subgraph cluster_Nachhaltigkeit {{
        label="Nachhaltigkeit & Zukunftsfaehigkeit"; fillcolor="#D5E8D4"; style=filled; penwidth=1; fontsize=11; fontname="Arial Bold";
        Nutzen [label="Nutzen der Ausbildung", shape=hexagon, fillcolor="#A3D9A5"];
        subgraph cluster_NutzenJungeMenschen {{
             label = "fuer Junge Menschen"; fillcolor="#E8F5E9"; style=filled; fontsize=10;
             EinstiegBeruf [label="Erleichterter
Berufseinstieg", shape=note];
              /* ... other benefits ... */
        }}
    }}

    // Edge Examples
    Hauptthema -> Wettbewerbsvorteil [xlabel="wichtigster Grund", penwidth=2, color=darkgreen, dir=forward];
    Hauptthema -> Handlungsfaehigkeit [xlabel="Hauptziel", penwidth=2, color=blue, dir=forward];
    Wettbewerbsvorteil -> Nachwuchssicherung [xlabel="durch", penwidth=1.5];
    Nachwuchssicherung -> KostenRekrutierung [xlabel="senkt"];
}}
        </code>
    </SimplifiedSyntaxExample>

    <InputText>
        <label>Eingabetext:</label>
        <content>
---
{text}
---
        </content>
    </InputText>

    <OutputFormatReminder>
        **Ausgabe:** Bitte gib NUR den vollständigen Graphviz `digraph` Code aus, ohne zusätzliche Erklärungen davor oder danach.
    </OutputFormatReminder>

</Prompt>'''


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


def list_ollama_models() -> List[Dict[str, Any]]:
    """
    Listet alle verfügbaren Ollama-Modelle auf.

    Returns:
        Liste von Modell-Informationen
    """
    try:
        import ollama
        models_response = ollama.list()
        models = models_response.get('models', [])
        return models
    except ImportError:
        print("Fehler: Ollama Python-Paket nicht installiert.")
        print("Installieren mit: pip install ollama")
        return []
    except Exception as e:
        print(f"Fehler beim Abrufen der Modelle: {e}")
        return []


def get_model_names() -> List[str]:
    """
    Gibt eine Liste der Namen aller verfügbaren Ollama-Modelle zurück.

    Returns:
        Liste von Modellnamen
    """
    models = list_ollama_models()
    return [m.get('name', m.get('model', '')) for m in models if m]


def print_available_models() -> List[str]:
    """
    Zeigt alle verfügbaren Ollama-Modelle an und gibt deren Namen zurück.

    Returns:
        Liste von Modellnamen
    """
    models = list_ollama_models()

    if not models:
        print("Keine Ollama-Modelle gefunden.")
        print("Stellen Sie sicher, dass Ollama läuft und Modelle installiert sind.")
        return []

    print("\nVerfügbare Ollama-Modelle:")
    print("-" * 50)

    model_names = []
    for i, model in enumerate(models, 1):
        name = model.get('name', model.get('model', 'Unknown'))
        size = model.get('size', 0)
        size_gb = size / (1024**3) if size else 0

        model_names.append(name)
        print(f"  [{i}] {name}")
        if size_gb > 0:
            print(f"      Größe: {size_gb:.1f} GB")

    print("-" * 50)
    return model_names


def select_models_interactive() -> List[str]:
    """
    Interaktive Auswahl von Modellen.

    Returns:
        Liste der ausgewählten Modellnamen
    """
    model_names = print_available_models()

    if not model_names:
        return []

    print("\nOptionen:")
    print("  - Nummern eingeben (z.B. '1,3,5' oder '1-3')")
    print("  - 'all' für alle Modelle")
    print("  - 'q' zum Abbrechen")

    while True:
        choice = input("\nAuswahl: ").strip().lower()

        if choice == 'q':
            return []

        if choice == 'all':
            return model_names

        # Parse die Auswahl
        selected = []
        try:
            parts = choice.replace(' ', '').split(',')
            for part in parts:
                if '-' in part:
                    # Range wie "1-3"
                    start, end = part.split('-')
                    for i in range(int(start), int(end) + 1):
                        if 1 <= i <= len(model_names):
                            selected.append(model_names[i - 1])
                else:
                    # Einzelne Nummer
                    idx = int(part)
                    if 1 <= idx <= len(model_names):
                        selected.append(model_names[idx - 1])

            if selected:
                # Entferne Duplikate, behalte Reihenfolge
                seen = set()
                unique = []
                for m in selected:
                    if m not in seen:
                        seen.add(m)
                        unique.append(m)
                return unique
            else:
                print("Keine gültige Auswahl. Bitte erneut versuchen.")

        except ValueError:
            print("Ungültige Eingabe. Bitte Nummern, Bereiche oder 'all' eingeben.")


def create_mindmap_prompt(text: str) -> str:
    """
    Erstellt den vollständigen Mindmap-Prompt mit dem eingegebenen Text.

    Args:
        text: Der zu analysierende Text

    Returns:
        Der vollständige Prompt
    """
    return MINDMAP_PROMPT_TEMPLATE.format(text=text)


def generate_mindmap(
    text: str,
    model: str,
    output_path: Optional[str] = None,
    output_dir: str = "./mindmaps"
) -> Dict[str, Any]:
    """
    Generiert eine Mindmap aus Text mit einem Ollama-Modell.

    Args:
        text: Der zu visualisierende Text
        model: Name des Ollama-Modells
        output_path: Optionaler Pfad für die PNG-Ausgabe
        output_dir: Verzeichnis für Ausgabedateien

    Returns:
        Dict mit Ergebnisinformationen
    """
    prompt = create_mindmap_prompt(text)
    result = test_ollama_model(model, prompt)

    if result["valid_graphviz"] and result["extracted_dot_code"]:
        os.makedirs(output_dir, exist_ok=True)

        if output_path is None:
            safe_model = model.replace(":", "_").replace("/", "_")
            output_path = os.path.join(output_dir, f"mindmap_{safe_model}.png")

        dot_path = output_path.replace('.png', '.dot')

        # Speichere DOT
        save_dot_file(result["extracted_dot_code"], dot_path)
        result["dot_path"] = dot_path

        # Rendere PNG
        render_result = render_dot_to_png(
            result["extracted_dot_code"],
            output_path,
            validate_first=False
        )
        result["png_path"] = output_path if render_result.success else None
        result["render_message"] = render_result.message

    return result


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

  # Liste verfügbare Ollama-Modelle
  python graphviz_tool.py list-models

  # Teste Ollama-Modelle (interaktiv)
  python graphviz_tool.py test-models --interactive --prompt "Create a graph"

  # Teste alle Ollama-Modelle
  python graphviz_tool.py test-models --all --prompt "Create a graph"

  # Teste spezifische Modelle
  python graphviz_tool.py test-models llama2 mistral --prompt "Create a graph"

  # Erstelle Mindmap aus Text
  python graphviz_tool.py mindmap --model llama2 --text "Ihr Text hier..."
  python graphviz_tool.py mindmap --model llama2 --file input.txt
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

    # List models command
    list_parser = subparsers.add_parser('list-models', help='Liste verfügbare Ollama-Modelle')

    # Test models command
    test_parser = subparsers.add_parser('test-models', help='Teste Ollama-Modelle auf Graphviz-Generierung')
    test_parser.add_argument('models', nargs='*', help='Zu testende Modelle (optional bei --all oder --interactive)')
    test_parser.add_argument('--prompt', '-p', required=True, help='Prompt für die Modelle')
    test_parser.add_argument('--output-dir', '-o', default='./model_tests', help='Ausgabeverzeichnis')
    test_parser.add_argument('--all', '-a', action='store_true', help='Teste alle verfügbaren Modelle')
    test_parser.add_argument('--interactive', '-i', action='store_true', help='Interaktive Modellauswahl')

    # Mindmap command
    mindmap_parser = subparsers.add_parser('mindmap', help='Erstelle Mindmap aus Text')
    mindmap_parser.add_argument('--model', '-m', help='Ollama-Modell (interaktiv wenn nicht angegeben)')
    mindmap_parser.add_argument('--text', '-t', help='Text für die Mindmap')
    mindmap_parser.add_argument('--file', '-f', help='Textdatei für die Mindmap')
    mindmap_parser.add_argument('--output', '-o', help='Ausgabe-PNG-Datei')
    mindmap_parser.add_argument('--output-dir', default='./mindmaps', help='Ausgabeverzeichnis')

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

    elif args.command == 'list-models':
        print_available_models()

    elif args.command == 'test-models':
        # Bestimme welche Modelle getestet werden sollen
        models_to_test = []

        if args.all:
            models_to_test = get_model_names()
            if not models_to_test:
                print("Keine Ollama-Modelle gefunden.")
                sys.exit(1)
            print(f"Teste alle {len(models_to_test)} verfügbaren Modelle...")

        elif args.interactive:
            models_to_test = select_models_interactive()
            if not models_to_test:
                print("Keine Modelle ausgewählt.")
                sys.exit(0)

        elif args.models:
            models_to_test = args.models

        else:
            print("Fehler: Bitte Modelle angeben, --all oder --interactive verwenden.")
            sys.exit(1)

        print(f"\nAusgewählte Modelle: {', '.join(models_to_test)}")

        results = test_multiple_models(models_to_test, args.prompt, args.output_dir)
        print_model_comparison(results)

        # Speichere Ergebnisse als JSON
        json_path = os.path.join(args.output_dir, "results.json")
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Ergebnisse gespeichert: {json_path}")

    elif args.command == 'mindmap':
        # Text ermitteln
        if args.text:
            text = args.text
        elif args.file:
            with open(args.file, 'r') as f:
                text = f.read()
        else:
            print("Text für Mindmap eingeben (beenden mit Ctrl+D oder leerer Zeile):")
            lines = []
            try:
                while True:
                    line = input()
                    if line == '':
                        break
                    lines.append(line)
            except EOFError:
                pass
            text = '\n'.join(lines)

        if not text.strip():
            print("Fehler: Kein Text angegeben.")
            sys.exit(1)

        # Modell ermitteln
        model = args.model
        if not model:
            print("\nKein Modell angegeben. Bitte wählen:")
            selected = select_models_interactive()
            if not selected:
                print("Kein Modell ausgewählt.")
                sys.exit(0)
            model = selected[0]

        print(f"\nGeneriere Mindmap mit Modell: {model}")
        print(f"Textlänge: {len(text)} Zeichen")

        result = generate_mindmap(
            text=text,
            model=model,
            output_path=args.output,
            output_dir=args.output_dir
        )

        if result["valid_graphviz"]:
            print(f"\n✓ Mindmap erfolgreich erstellt!")
            if result.get("png_path"):
                print(f"  PNG: {result['png_path']}")
            if result.get("dot_path"):
                print(f"  DOT: {result['dot_path']}")
        else:
            print(f"\n✗ Mindmap-Generierung fehlgeschlagen")
            if result.get("error"):
                print(f"  Fehler: {result['error']}")
            if result.get("validation_errors"):
                print("  Validierungsfehler:")
                for err in result["validation_errors"][:5]:
                    print(f"    - {err}")

            # Zeige rohe Antwort für Debugging
            if result.get("response"):
                print("\n  Rohe Modell-Antwort (erste 500 Zeichen):")
                print(f"  {result['response'][:500]}...")

        sys.exit(0 if result["valid_graphviz"] else 1)

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
