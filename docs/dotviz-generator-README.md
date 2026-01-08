# Graphviz Visualization Tool

Ein Python-CLI-Tool zur Erstellung, Validierung und Rendering von Graphviz-Diagrammen. Unterstützt automatische Mindmap-Generierung via Ollama LLMs.

## Features

- **DOT-Validierung**: Syntaxprüfung vor dem Rendern
- **PNG-Rendering**: Direkte Konvertierung von DOT zu PNG
- **Ollama-Integration**: Teste LLM-Modelle auf ihre Graphviz-Code-Generierungsfähigkeit
- **Mindmap-Generierung**: Automatische Mindmap-Erstellung aus Text via LLM
- **Interaktive Modellauswahl**: Wähle Ollama-Modelle per Menü

## Installation

### Voraussetzungen

```bash
# Graphviz installieren
apt-get install graphviz  # Ubuntu/Debian
brew install graphviz     # macOS

# Python-Abhängigkeiten
pip install ollama
```

## Verwendung

### Grundbefehle

```bash
# Hilfe anzeigen
python graphviz_tool.py --help

# DOT-Datei validieren
python graphviz_tool.py validate input.dot
python graphviz_tool.py validate -  # von stdin

# DOT zu PNG rendern
python graphviz_tool.py render input.dot output.png
python graphviz_tool.py render input.dot output.png --no-validate

# Beispiel-Graph erstellen
python graphviz_tool.py example --output example.png --dot-output example.dot

# Flowchart aus Schritten erstellen
python graphviz_tool.py flowchart "Start" "Prozess" "Ende" -o flow.png
```

### Ollama-Modell-Tests

```bash
# Verfügbare Modelle anzeigen
python graphviz_tool.py list-models

# Interaktive Modellauswahl
python graphviz_tool.py test-models --interactive -p "Erstelle einen Graphen für einen Login-Prozess"

# Alle Modelle testen
python graphviz_tool.py test-models --all -p "Create a simple flowchart"

# Spezifische Modelle testen
python graphviz_tool.py test-models llama2 mistral codellama -p "Create a graph"
```

### Mindmap-Generierung

```bash
# Mit Text direkt
python graphviz_tool.py mindmap -m llama2 -t "Ihr Text hier..."

# Aus Datei
python graphviz_tool.py mindmap -m llama2 -f document.txt

# Interaktiv (Modellauswahl + Text-Eingabe)
python graphviz_tool.py mindmap

# Mit benutzerdefiniertem Ausgabepfad
python graphviz_tool.py mindmap -m mistral -f input.txt -o meine_mindmap.png
```

## Mindmap-Prompt

Das Tool enthält einen optimierten Prompt für Level-3-Mindmaps mit:

- **Farbcodierte Cluster**:
  - Gelb/Orange (`#FFF3CD`, `#FFEBCD`): Gründe, Basis
  - Blau (`#DAE8FC`, `#EBF5FB`): Ziele, Kompetenzen
  - Grün (`#D5E8D4`, `#E8F5E9`): Nutzen, Nachhaltigkeit

- **Visuelle Hierarchie**:
  - Hauptthema: `shape=doubleoctagon`, `penwidth=2`
  - Wichtige Knoten: `penwidth=1.5-2`
  - Beziehungen via `xlabel` (nicht `label`)

- **Automatische Umlaut-Ersetzung**: ä→ae, ö→oe, ü→ue, ß→ss

## API-Funktionen

```python
from graphviz_tool import (
    validate_dot_code,
    render_dot_to_png,
    test_ollama_model,
    generate_mindmap,
    list_ollama_models,
    get_model_names,
    create_flowchart,
    create_hierarchy
)

# Validierung
is_valid, errors = validate_dot_code(dot_code)

# Rendern
result = render_dot_to_png(dot_code, "output.png", validate_first=True)

# Ollama-Test
result = test_ollama_model("llama2", "Create a graph for...")

# Mindmap generieren
result = generate_mindmap(
    text="Ihr Text...",
    model="llama2",
    output_path="mindmap.png"
)

# Verfügbare Modelle
models = get_model_names()  # ["llama2:latest", "mistral:latest", ...]
```

## Ausgabestruktur

```
./model_tests/           # Test-Ergebnisse
  ├── results.json       # JSON mit allen Testergebnissen
  ├── llama2_output.dot  # Generierter DOT-Code
  └── llama2_output.png  # Gerendertes Diagramm

./mindmaps/              # Generierte Mindmaps
  ├── mindmap_llama2.dot
  └── mindmap_llama2.png
```

## Modell-Vergleich

Das Tool zeigt nach Tests eine Vergleichstabelle:

```
============================================================
MODELL-VERGLEICH: Graphviz-Code-Generierung
============================================================

Ergebnis: 2/3 Modelle generierten validen Code

  ✓ llama2:latest
      PNG: ./model_tests/llama2_latest_output.png
  ✓ mistral:latest
      PNG: ./model_tests/mistral_latest_output.png
  ✗ phi:latest
      Validierungsfehler: syntax error in line 5
```

## Hinweise

- **Ollama muss laufen**: Für LLM-Funktionen muss der Ollama-Server aktiv sein
- **Graphviz erforderlich**: Das `dot`-Binary muss im PATH sein
- **Validierung empfohlen**: Immer `validate_first=True` nutzen um Fehler früh zu erkennen

## Verwandte Tools

Für Cloud-Architektur-Diagramme mit Provider-Icons (AWS, Azure, GCP) siehe:
- [diagrams](https://github.com/mingrammer/diagrams) - Diagram as Code für Cloud-Architekturen
