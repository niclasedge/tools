#!/usr/bin/env python3
"""
Diagram Agent - Gradio Web Interface

Interactive web UI for generating diagrams with AI.
"""

import gradio as gr
from pathlib import Path
import tempfile
import os

from .orchestrator import DiagramOrchestrator, quick_diagram
from .tools import validate_diagram, render_diagram, DiagramFormat


# ============== State ==============

class AppState:
    """Application state."""
    def __init__(self):
        self.current_code = ""
        self.current_format = "graphviz"
        self.history = []

state = AppState()


# ============== Core Functions ==============

def generate_diagram(
    description: str,
    format_type: str,
    model: str,
    quick_mode: bool
) -> tuple:
    """
    Generate a diagram from description.

    Returns: (image_path, code, status_message, validation_info)
    """
    if not description.strip():
        return None, "", "⚠️ Bitte Beschreibung eingeben", ""

    try:
        if quick_mode:
            # Quick mode - single pass
            code = quick_diagram(description, format_type)
            validation = validate_diagram(code, format_type)

            if validation.valid:
                # Render to temp file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    output_path = f.name

                result = render_diagram(code, output_path, DiagramFormat(format_type))

                if result.success:
                    state.current_code = code
                    state.history.append({"desc": description[:50], "code": code})
                    return (
                        output_path,
                        code,
                        f"✅ Erfolgreich generiert ({format_type})",
                        "✓ Validierung bestanden"
                    )
                else:
                    return None, code, f"⚠️ Render-Fehler: {result.error}", ""
            else:
                errors = "\n".join(f"• {e}" for e in validation.errors)
                return None, code, "⚠️ Code ungültig", f"Fehler:\n{errors}"

        else:
            # Full pipeline mode
            orchestrator = DiagramOrchestrator(
                model_name=model,
                output_dir=tempfile.gettempdir(),
                preferred_format=format_type,
                max_improvement_iterations=3
            )

            result = orchestrator.run(description)

            if result.success:
                state.current_code = result.diagram_code
                state.history.append({"desc": description[:50], "code": result.diagram_code})

                validation_info = f"✓ Format: {result.format.value}\n"
                validation_info += f"✓ Iterationen: {result.iterations}\n"
                validation_info += f"✓ Dauer: {result.duration_seconds:.1f}s"

                return (
                    result.output_path,
                    result.diagram_code,
                    f"✅ Erfolgreich! ({result.duration_seconds:.1f}s)",
                    validation_info
                )
            else:
                errors = "\n".join(f"• {e}" for e in result.errors)
                return (
                    None,
                    result.diagram_code or "",
                    f"❌ Generierung fehlgeschlagen nach {result.iterations} Versuchen",
                    f"Fehler:\n{errors}"
                )

    except Exception as e:
        return None, "", f"❌ Fehler: {str(e)}", ""


def validate_code(code: str) -> tuple:
    """Validate diagram code."""
    if not code.strip():
        return "⚠️ Kein Code zum Validieren", ""

    result = validate_diagram(code)

    if result.valid:
        return f"✅ Valider {result.format.value} Code", ""
    else:
        errors = "\n".join(f"• {e}" for e in result.errors)
        suggestions = "\n".join(f"💡 {s}" for s in result.suggestions) if result.suggestions else ""
        return f"❌ Ungültiger {result.format.value} Code", f"Fehler:\n{errors}\n\n{suggestions}"


def render_code(code: str, format_type: str) -> tuple:
    """Render existing code to image."""
    if not code.strip():
        return None, "⚠️ Kein Code zum Rendern"

    # Validate first
    validation = validate_diagram(code, format_type)
    if not validation.valid:
        errors = ", ".join(validation.errors[:2])
        return None, f"❌ Code ungültig: {errors}"

    # Render
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        output_path = f.name

    result = render_diagram(code, output_path, DiagramFormat(format_type))

    if result.success:
        return output_path, "✅ Gerendert"
    else:
        return None, f"❌ Render-Fehler: {result.error}"


def get_example_prompt(example_type: str) -> str:
    """Get an example prompt."""
    examples = {
        "Pipeline": "A data pipeline: Input -> Validate -> Process -> Transform -> Output -> Database",
        "Microservices": "Microservices architecture: API Gateway connects to User Service, Order Service, Payment Service. All services connect to PostgreSQL database.",
        "Flowchart": "User login flow: Start -> Enter credentials -> Validate -> If valid go to Dashboard, else show Error and retry -> End",
        "System": "Web application architecture: Browser -> Load Balancer -> Web Servers (3x) -> Cache (Redis) -> Database (PostgreSQL) -> Backup Storage",
    }
    return examples.get(example_type, "")


# ============== UI ==============

def create_ui():
    """Create the Gradio interface."""

    with gr.Blocks(
        title="Diagram Agent",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
        ),
        css="""
        .container { max-width: 1400px; margin: auto; }
        .header { text-align: center; margin-bottom: 1rem; }
        .code-box { font-family: monospace; }
        """
    ) as app:

        gr.Markdown("""
        # 🎨 Diagram Agent
        **Multi-Agent Diagram Generation mit Google ADK + Ollama**

        Beschreibe dein Diagramm in natürlicher Sprache und der Agent generiert es automatisch.
        """)

        with gr.Row():
            # Left column - Input
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Eingabe")

                description = gr.Textbox(
                    label="Diagramm-Beschreibung",
                    placeholder="Beschreibe das Diagramm, das du erstellen möchtest...",
                    lines=4
                )

                with gr.Row():
                    format_type = gr.Dropdown(
                        choices=["graphviz", "mermaid", "plantuml"],
                        value="graphviz",
                        label="Format"
                    )
                    model = gr.Dropdown(
                        choices=["gemma3:4b", "qwen2.5-coder:7b", "mistral:7b", "gpt-oss:latest"],
                        value="gemma3:4b",
                        label="Modell"
                    )

                quick_mode = gr.Checkbox(
                    label="⚡ Quick Mode (schneller, aber ohne Verbesserungs-Loop)",
                    value=True
                )

                generate_btn = gr.Button("🚀 Generieren", variant="primary", size="lg")

                gr.Markdown("### 💡 Beispiele")
                with gr.Row():
                    ex_pipeline = gr.Button("Pipeline", size="sm")
                    ex_micro = gr.Button("Microservices", size="sm")
                    ex_flow = gr.Button("Flowchart", size="sm")
                    ex_system = gr.Button("System", size="sm")

                status = gr.Textbox(label="Status", interactive=False)

            # Right column - Output
            with gr.Column(scale=1):
                gr.Markdown("### 🖼️ Ausgabe")

                output_image = gr.Image(
                    label="Generiertes Diagramm",
                    type="filepath",
                    height=400
                )

                validation_info = gr.Textbox(
                    label="Validierung",
                    interactive=False,
                    lines=3
                )

        # Code section
        gr.Markdown("### 💻 Code")

        with gr.Row():
            with gr.Column(scale=2):
                code_output = gr.Textbox(
                    label="Diagram Code",
                    lines=12,
                    max_lines=20,
                    show_copy_button=True
                )

            with gr.Column(scale=1):
                with gr.Row():
                    validate_btn = gr.Button("✓ Validieren")
                    render_btn = gr.Button("🖼️ Rendern")

                code_status = gr.Textbox(label="Code Status", interactive=False, lines=4)

        # Event handlers
        generate_btn.click(
            fn=generate_diagram,
            inputs=[description, format_type, model, quick_mode],
            outputs=[output_image, code_output, status, validation_info]
        )

        validate_btn.click(
            fn=validate_code,
            inputs=[code_output],
            outputs=[status, code_status]
        )

        render_btn.click(
            fn=render_code,
            inputs=[code_output, format_type],
            outputs=[output_image, status]
        )

        # Example buttons
        ex_pipeline.click(fn=lambda: get_example_prompt("Pipeline"), outputs=[description])
        ex_micro.click(fn=lambda: get_example_prompt("Microservices"), outputs=[description])
        ex_flow.click(fn=lambda: get_example_prompt("Flowchart"), outputs=[description])
        ex_system.click(fn=lambda: get_example_prompt("System"), outputs=[description])

        gr.Markdown("""
        ---
        **Tipps:**
        - Graphviz eignet sich für komplexe Diagramme mit vielen Verbindungen
        - Mermaid ist einfacher und gut für Flowcharts
        - Quick Mode ist schneller, Full Mode versucht Fehler automatisch zu korrigieren
        """)

    return app


# ============== Main ==============

def main():
    """Launch the Gradio app."""
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
