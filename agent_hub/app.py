#!/usr/bin/env python3
"""
Agent Hub - Combined Gradio Frontend

Single interface for all AI agents:
- Diagram Agent: Generate diagrams from text
- Health Agent: Meal planning and nutrition
"""

import sys
from pathlib import Path

# Add parent directories to path
tools_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tools_dir / "diagram_agent"))
sys.path.insert(0, str(tools_dir / "health-agent"))

import gradio as gr
from typing import Tuple, List
import tempfile

# ============== Diagram Agent Imports ==============
try:
    from orchestrator import DiagramOrchestrator, quick_diagram
    from tools import validate_diagram, render_diagram, DiagramFormat
    DIAGRAM_AVAILABLE = True
except ImportError as e:
    print(f"Diagram Agent not available: {e}")
    DIAGRAM_AVAILABLE = False

# ============== Health Agent Imports ==============
try:
    from orchestrator import HealthOrchestrator
    from api_client import FoodAPIClient, get_client, Product
    HEALTH_AVAILABLE = True
except ImportError as e:
    print(f"Health Agent not available: {e}")
    HEALTH_AVAILABLE = False


# ============== Diagram Agent Functions ==============

def generate_diagram(
    description: str,
    format_type: str,
    model: str,
    quick_mode: bool
) -> tuple:
    """Generate a diagram from description."""
    if not DIAGRAM_AVAILABLE:
        return None, "", "Diagram Agent nicht verfügbar", ""

    if not description.strip():
        return None, "", "Bitte Beschreibung eingeben", ""

    try:
        if quick_mode:
            code = quick_diagram(description, format_type)
            validation = validate_diagram(code, format_type)

            if validation.valid:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    output_path = f.name

                result = render_diagram(code, output_path, DiagramFormat(format_type))

                if result.success:
                    return (
                        output_path,
                        code,
                        f"Erfolgreich generiert ({format_type})",
                        "Validierung bestanden"
                    )
                else:
                    return None, code, f"Render-Fehler: {result.error}", ""
            else:
                errors = "\n".join(f"• {e}" for e in validation.errors)
                return None, code, "Code ungültig", f"Fehler:\n{errors}"
        else:
            orchestrator = DiagramOrchestrator(
                model_name=model,
                output_dir=tempfile.gettempdir(),
                preferred_format=format_type,
                max_improvement_iterations=3
            )

            result = orchestrator.run(description)

            if result.success:
                validation_info = f"Format: {result.format.value}\n"
                validation_info += f"Iterationen: {result.iterations}\n"
                validation_info += f"Dauer: {result.duration_seconds:.1f}s"

                return (
                    result.output_path,
                    result.diagram_code,
                    f"Erfolgreich! ({result.duration_seconds:.1f}s)",
                    validation_info
                )
            else:
                errors = "\n".join(f"• {e}" for e in result.errors)
                return (
                    None,
                    result.diagram_code or "",
                    f"Fehlgeschlagen nach {result.iterations} Versuchen",
                    f"Fehler:\n{errors}"
                )

    except Exception as e:
        return None, "", f"Fehler: {str(e)}", ""


def validate_diagram_code(code: str) -> tuple:
    """Validate diagram code."""
    if not DIAGRAM_AVAILABLE:
        return "Diagram Agent nicht verfügbar", ""

    if not code.strip():
        return "Kein Code zum Validieren", ""

    result = validate_diagram(code)

    if result.valid:
        return f"Valider {result.format.value} Code", ""
    else:
        errors = "\n".join(f"• {e}" for e in result.errors)
        suggestions = "\n".join(f"• {s}" for s in result.suggestions) if result.suggestions else ""
        return f"Ungültiger {result.format.value} Code", f"Fehler:\n{errors}\n\n{suggestions}"


def render_diagram_code(code: str, format_type: str) -> tuple:
    """Render existing code to image."""
    if not DIAGRAM_AVAILABLE:
        return None, "Diagram Agent nicht verfügbar"

    if not code.strip():
        return None, "Kein Code zum Rendern"

    validation = validate_diagram(code, format_type)
    if not validation.valid:
        errors = ", ".join(validation.errors[:2])
        return None, f"Code ungültig: {errors}"

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        output_path = f.name

    result = render_diagram(code, output_path, DiagramFormat(format_type))

    if result.success:
        return output_path, "Gerendert"
    else:
        return None, f"Render-Fehler: {result.error}"


# ============== Health Agent Functions ==============

class HealthState:
    """Health agent state."""
    def __init__(self):
        self.orchestrator = None
        self.api_client = None

    def init(self, model: str = "gemma3:4b"):
        if HEALTH_AVAILABLE:
            self.orchestrator = HealthOrchestrator(model_name=model)
            self.api_client = get_client()

health_state = HealthState()


def search_products(query: str, store: str) -> Tuple[str, str]:
    """Search for products."""
    if not HEALTH_AVAILABLE:
        return "", "Health Agent nicht verfügbar"

    if not query.strip():
        return "", "Bitte Suchbegriff eingeben"

    try:
        if health_state.api_client is None:
            health_state.api_client = get_client()

        store_filter = None if store == "Alle" else store
        products = health_state.api_client.search(query, store_filter)

        if not products:
            return "", f"Keine Produkte gefunden für '{query}'"

        result = f"## Suchergebnisse: {query}\n\n"
        result += f"Gefunden: **{len(products)}** Produkte\n\n"
        result += "| Produkt | Store | Yuka Score |\n"
        result += "|---------|-------|------------|\n"

        for p in products[:20]:
            score = f"{p.yuka_score}" if p.yuka_score else "-"
            result += f"| {p.name[:40]} | {p.store} | {score} |\n"

        return result, f"Gefunden: {len(products)} Produkte"

    except Exception as e:
        return "", f"Fehler: {e}"


def get_healthy_products(store: str) -> Tuple[str, str]:
    """Get healthy product recommendations."""
    if not HEALTH_AVAILABLE:
        return "", "Health Agent nicht verfügbar"

    try:
        if health_state.api_client is None:
            health_state.api_client = get_client()

        store_filter = None if store == "Alle" else store
        products = health_state.api_client.get_healthy_products(store_filter, min_score=70, limit=30)

        if not products:
            return "", "Keine gesunden Produkte gefunden"

        result = "## Top Gesunde Produkte (Yuka Score 70+)\n\n"
        result += "| Produkt | Store | Score | Kalorien | Protein |\n"
        result += "|---------|-------|-------|----------|--------|\n"

        for p in products:
            cal = f"{p.calories:.0f}" if p.calories else "-"
            prot = f"{p.protein:.1f}g" if p.protein else "-"
            result += f"| {p.name[:40]} | {p.store} | {p.yuka_score} | {cal} | {prot} |\n"

        return result, f"{len(products)} gesunde Produkte gefunden"

    except Exception as e:
        return "", f"Fehler: {e}"


def create_meal_plan(diet_type: str, calories: int, preferences: str, model: str) -> Tuple[str, str]:
    """Create a weekly meal plan."""
    if not HEALTH_AVAILABLE:
        return "", "Health Agent nicht verfügbar"

    try:
        if health_state.orchestrator is None or health_state.orchestrator.model_name != model:
            health_state.init(model)

        health_state.orchestrator.diet_type = diet_type.lower()
        health_state.orchestrator.target_calories = calories

        result = health_state.orchestrator.create_week_plan(preferences, diet_type.lower(), calories)

        if result.success:
            return result.content, f"Wochenplan erstellt ({result.duration_seconds:.1f}s)"
        else:
            return "", f"Fehler: {', '.join(result.errors)}"

    except Exception as e:
        return "", f"Fehler: {e}"


def create_recipe(dish_name: str, ingredients: str, diet_type: str, max_time: int, model: str) -> Tuple[str, str]:
    """Create a recipe."""
    if not HEALTH_AVAILABLE:
        return "", "Health Agent nicht verfügbar"

    try:
        if health_state.orchestrator is None:
            health_state.init(model)

        ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()] if ingredients else None

        result = health_state.orchestrator.create_recipe(
            dish_name=dish_name,
            ingredients=ingredient_list,
            diet_type=diet_type.lower(),
            max_time=max_time
        )

        if result.success:
            return result.content, f"Rezept erstellt ({result.duration_seconds:.1f}s)"
        else:
            return "", f"Fehler: {', '.join(result.errors)}"

    except Exception as e:
        return "", f"Fehler: {e}"


# ============== UI ==============

def create_ui():
    """Create the combined Gradio interface."""

    with gr.Blocks(
        title="Agent Hub",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="emerald",
        ),
        css="""
        .container { max-width: 1400px; margin: auto; }
        """
    ) as app:

        gr.Markdown("""
        # Agent Hub
        **KI-Agenten für Diagramme, Ernährung und mehr**
        """)

        with gr.Row():
            model_select = gr.Dropdown(
                choices=["gemma3:4b", "qwen2.5-coder:7b", "mistral:7b", "gpt-oss:latest"],
                value="gemma3:4b",
                label="KI-Modell",
                scale=1
            )
            status_display = gr.Textbox(
                value=f"Diagram: {'OK' if DIAGRAM_AVAILABLE else 'N/A'} | Health: {'OK' if HEALTH_AVAILABLE else 'N/A'}",
                label="Status",
                interactive=False,
                scale=2
            )

        with gr.Tabs():
            # ========== DIAGRAM AGENT TAB ==========
            with gr.Tab("Diagramme"):
                gr.Markdown("### Diagramm-Generator")

                with gr.Row():
                    with gr.Column(scale=1):
                        diagram_description = gr.Textbox(
                            label="Beschreibung",
                            placeholder="Beschreibe das Diagramm...",
                            lines=4
                        )

                        with gr.Row():
                            diagram_format = gr.Dropdown(
                                choices=["graphviz", "mermaid", "plantuml"],
                                value="graphviz",
                                label="Format"
                            )
                            quick_mode = gr.Checkbox(
                                label="Quick Mode",
                                value=True
                            )

                        diagram_btn = gr.Button("Generieren", variant="primary")

                        gr.Markdown("**Beispiele:**")
                        with gr.Row():
                            ex1 = gr.Button("Pipeline", size="sm")
                            ex2 = gr.Button("Microservices", size="sm")
                            ex3 = gr.Button("Flowchart", size="sm")

                        diagram_status = gr.Textbox(label="Status", interactive=False)

                    with gr.Column(scale=1):
                        diagram_image = gr.Image(label="Diagramm", type="filepath", height=400)
                        diagram_validation = gr.Textbox(label="Validierung", interactive=False, lines=3)

                diagram_code = gr.Textbox(label="Code", lines=8, show_copy_button=True)

                # Diagram event handlers
                diagram_btn.click(
                    fn=generate_diagram,
                    inputs=[diagram_description, diagram_format, model_select, quick_mode],
                    outputs=[diagram_image, diagram_code, diagram_status, diagram_validation]
                )

                ex1.click(fn=lambda: "Data pipeline: Input -> Validate -> Process -> Transform -> Output -> Database", outputs=[diagram_description])
                ex2.click(fn=lambda: "Microservices: API Gateway -> User Service, Order Service, Payment Service. All connect to PostgreSQL.", outputs=[diagram_description])
                ex3.click(fn=lambda: "Login flow: Start -> Enter credentials -> Validate -> If valid: Dashboard, else: Error -> Retry", outputs=[diagram_description])

            # ========== HEALTH AGENT TAB ==========
            with gr.Tab("Ernährung"):
                with gr.Tabs():
                    # Products Sub-Tab
                    with gr.Tab("Produkte"):
                        gr.Markdown("### Produktsuche (Lidl/Aldi)")

                        with gr.Row():
                            search_query = gr.Textbox(
                                label="Suchbegriff",
                                placeholder="z.B. Joghurt, Hähnchen...",
                                scale=2
                            )
                            search_store = gr.Dropdown(
                                choices=["Alle", "Lidl", "Aldi-sud"],
                                value="Alle",
                                label="Store",
                                scale=1
                            )

                        with gr.Row():
                            search_btn = gr.Button("Suchen", variant="primary")
                            healthy_btn = gr.Button("Gesunde Produkte")

                        search_results = gr.Markdown(label="Ergebnisse")
                        search_status = gr.Textbox(label="Status", interactive=False)

                        search_btn.click(
                            fn=search_products,
                            inputs=[search_query, search_store],
                            outputs=[search_results, search_status]
                        )

                        healthy_btn.click(
                            fn=get_healthy_products,
                            inputs=[search_store],
                            outputs=[search_results, search_status]
                        )

                    # Meal Plan Sub-Tab
                    with gr.Tab("Wochenplan"):
                        gr.Markdown("### Wochenplan erstellen")

                        with gr.Row():
                            diet_type = gr.Dropdown(
                                choices=["Balanced", "Low-Carb", "Keto", "High-Protein"],
                                value="Balanced",
                                label="Ernährungstyp"
                            )
                            calories = gr.Slider(
                                minimum=1200,
                                maximum=3500,
                                value=2000,
                                step=100,
                                label="Kalorien/Tag"
                            )

                        preferences = gr.Textbox(
                            label="Präferenzen",
                            placeholder="z.B. vegetarisch, keine Nüsse...",
                            lines=2
                        )

                        plan_btn = gr.Button("Wochenplan erstellen", variant="primary")

                        meal_plan_output = gr.Markdown(label="Wochenplan")
                        plan_status = gr.Textbox(label="Status", interactive=False)

                        plan_btn.click(
                            fn=create_meal_plan,
                            inputs=[diet_type, calories, preferences, model_select],
                            outputs=[meal_plan_output, plan_status]
                        )

                    # Recipe Sub-Tab
                    with gr.Tab("Rezepte"):
                        gr.Markdown("### Rezept erstellen")

                        with gr.Row():
                            dish_name = gr.Textbox(
                                label="Gericht",
                                placeholder="z.B. Hähnchen Curry...",
                                scale=2
                            )
                            recipe_diet = gr.Dropdown(
                                choices=["Balanced", "Low-Carb", "Keto", "High-Protein"],
                                value="Balanced",
                                label="Ernährungstyp",
                                scale=1
                            )

                        ingredients_input = gr.Textbox(
                            label="Zutaten (optional)",
                            placeholder="Hähnchen, Paprika, Reis...",
                            lines=2
                        )

                        max_time = gr.Slider(
                            minimum=10,
                            maximum=120,
                            value=30,
                            step=5,
                            label="Max. Zeit (Min)"
                        )

                        recipe_btn = gr.Button("Rezept erstellen", variant="primary")

                        recipe_output = gr.Markdown(label="Rezept")
                        recipe_status = gr.Textbox(label="Status", interactive=False)

                        recipe_btn.click(
                            fn=create_recipe,
                            inputs=[dish_name, ingredients_input, recipe_diet, max_time, model_select],
                            outputs=[recipe_output, recipe_status]
                        )

        gr.Markdown("---\n*Agent Hub v0.1 - Diagram Agent + Health Agent*")

    return app


# ============== Main ==============

def main():
    """Launch the combined app."""
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
