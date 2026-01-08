#!/bin/bash
#
# Agent Hub - Schnellstart
# Startet das kombinierte Frontend für Diagram + Health Agents
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=${1:-7860}

echo "==================================="
echo "  Agent Hub - Gradio Frontend"
echo "==================================="
echo ""
echo "Starte auf Port $PORT..."
echo "URL: http://localhost:$PORT"
echo ""
echo "Agents:"
echo "  - Diagram Agent (Graphviz/Mermaid/PlantUML)"
echo "  - Health Agent (Wochenplan/Rezepte/Produkte)"
echo ""
echo "Beenden mit Ctrl+C"
echo "-----------------------------------"

cd "$SCRIPT_DIR"
python3 agent_hub/app.py
