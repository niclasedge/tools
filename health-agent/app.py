#!/usr/bin/env python3
"""
Health Agent - Gradio Web Interface

Interactive web UI for meal planning, recipes, and nutrition.
"""

import gradio as gr
from typing import Tuple, List

try:
    from .orchestrator import HealthOrchestrator
    from .api_client import FoodAPIClient, get_client, Product
except ImportError:
    from orchestrator import HealthOrchestrator
    from api_client import FoodAPIClient, get_client, Product


# ============== State ==============

class AppState:
    """Application state."""
    def __init__(self):
        self.orchestrator = None
        self.api_client = None
        self.current_plan = ""
        self.favorites = []

    def init(self, model: str = "gemma3:4b"):
        """Initialize clients."""
        self.orchestrator = HealthOrchestrator(model_name=model)
        self.api_client = get_client()

state = AppState()


# ============== Core Functions ==============

def init_clients(model: str) -> str:
    """Initialize API clients."""
    try:
        state.init(model)
        return "Verbunden"
    except Exception as e:
        return f"Fehler: {e}"


def search_products(
    query: str,
    store: str,
    category: str
) -> Tuple[str, str]:
    """Search for products."""
    if not query.strip():
        return "", "Bitte Suchbegriff eingeben"

    try:
        if state.api_client is None:
            state.api_client = get_client()

        store_filter = None if store == "Alle" else store
        products = state.api_client.search(query, store_filter)

        if not products:
            return "", f"Keine Produkte gefunden für '{query}'"

        # Format results as markdown table
        result = f"## Suchergebnisse: {query}\n\n"
        result += f"Gefunden: **{len(products)}** Produkte\n\n"
        result += "| Produkt | Store | Kalorien | Protein | Carbs | Score |\n"
        result += "|---------|-------|----------|---------|-------|-------|\n"

        for p in products[:20]:
            cal = f"{p.calories:.0f}" if p.calories else "-"
            prot = f"{p.protein:.1f}g" if p.protein else "-"
            carb = f"{p.carbs:.1f}g" if p.carbs else "-"
            score = f"{p.yuka_score}" if p.yuka_score else "-"
            result += f"| {p.name[:40]} | {p.store} | {cal} | {prot} | {carb} | {score} |\n"

        return result, f"Gefunden: {len(products)} Produkte"

    except Exception as e:
        return "", f"Fehler: {e}"


def create_meal_plan(
    diet_type: str,
    calories: int,
    preferences: str,
    model: str
) -> Tuple[str, str]:
    """Create a weekly meal plan."""
    try:
        if state.orchestrator is None or state.orchestrator.model_name != model:
            state.init(model)

        state.orchestrator.diet_type = diet_type.lower()
        state.orchestrator.target_calories = calories

        result = state.orchestrator.create_week_plan(preferences, diet_type.lower(), calories)

        if result.success:
            state.current_plan = result.content
            return result.content, f"Wochenplan erstellt ({result.duration_seconds:.1f}s)"
        else:
            return "", f"Fehler: {', '.join(result.errors)}"

    except Exception as e:
        return "", f"Fehler: {e}"


def create_recipe(
    dish_name: str,
    ingredients: str,
    diet_type: str,
    max_time: int,
    model: str
) -> Tuple[str, str]:
    """Create a recipe."""
    try:
        if state.orchestrator is None:
            state.init(model)

        ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()] if ingredients else None

        result = state.orchestrator.create_recipe(
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


def analyze_nutrition(
    meal_description: str,
    model: str
) -> Tuple[str, str]:
    """Analyze nutrition of a meal."""
    if not meal_description.strip():
        return "", "Bitte Mahlzeit beschreiben"

    try:
        if state.orchestrator is None:
            state.init(model)

        result = state.orchestrator.analyze_nutrition(meal_description)

        if result.success:
            return result.content, f"Analyse abgeschlossen ({result.duration_seconds:.1f}s)"
        else:
            return "", f"Fehler: {', '.join(result.errors)}"

    except Exception as e:
        return "", f"Fehler: {e}"


def get_healthy_products(store: str, category: str) -> Tuple[str, str]:
    """Get healthy product recommendations."""
    try:
        if state.api_client is None:
            state.api_client = get_client()

        store_filter = None if store == "Alle" else store
        products = state.api_client.get_healthy_products(store_filter, min_score=70, limit=30)

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


def get_favorites() -> Tuple[str, str]:
    """Get user favorites."""
    try:
        if state.api_client is None:
            state.api_client = get_client()

        products = state.api_client.get_favorites()

        if not products:
            return "Keine Favoriten gespeichert.", "0 Favoriten"

        result = "## Meine Favoriten\n\n"
        result += "| Produkt | Store | Kalorien | Protein |\n"
        result += "|---------|-------|----------|--------|\n"

        for p in products:
            cal = f"{p.calories:.0f}" if p.calories else "-"
            prot = f"{p.protein:.1f}g" if p.protein else "-"
            result += f"| {p.name[:40]} | {p.store} | {cal} | {prot} |\n"

        return result, f"{len(products)} Favoriten"

    except Exception as e:
        return "", f"Fehler: {e}"


# ============== UI ==============

def create_ui():
    """Create the Gradio interface."""

    with gr.Blocks(
        title="Health Agent",
        theme=gr.themes.Soft(
            primary_hue="green",
            secondary_hue="emerald",
        ),
        css="""
        .container { max-width: 1400px; margin: auto; }
        .header { text-align: center; margin-bottom: 1rem; }
        """
    ) as app:

        gr.Markdown("""
        # Health Agent
        **KI-gestützte Ernährungsplanung mit Lidl & Aldi Produkten**

        Erstelle Wochenpläne, finde Rezepte und analysiere Nährwerte.
        """)

        with gr.Row():
            model_select = gr.Dropdown(
                choices=["gemma3:4b", "qwen2.5-coder:7b", "mistral:7b"],
                value="gemma3:4b",
                label="KI-Modell",
                scale=1
            )
            connection_status = gr.Textbox(
                label="Status",
                value="Nicht verbunden",
                interactive=False,
                scale=1
            )
            connect_btn = gr.Button("Verbinden", scale=1)

        with gr.Tabs():
            # Tab 1: Product Search
            with gr.Tab("Produkte"):
                gr.Markdown("### Produktsuche")

                with gr.Row():
                    search_query = gr.Textbox(
                        label="Suchbegriff",
                        placeholder="z.B. Joghurt, Hähnchen, Milch...",
                        scale=2
                    )
                    search_store = gr.Dropdown(
                        choices=["Alle", "Lidl", "Aldi-sud"],
                        value="Alle",
                        label="Store",
                        scale=1
                    )
                    search_category = gr.Dropdown(
                        choices=["Alle", "dairy", "meat", "vegetables", "fruits", "bread", "beverages"],
                        value="Alle",
                        label="Kategorie",
                        scale=1
                    )

                with gr.Row():
                    search_btn = gr.Button("Suchen", variant="primary")
                    healthy_btn = gr.Button("Gesunde Produkte")
                    favorites_btn = gr.Button("Favoriten")

                search_results = gr.Markdown(label="Ergebnisse")
                search_status = gr.Textbox(label="Status", interactive=False)

            # Tab 2: Meal Planning
            with gr.Tab("Wochenplan"):
                gr.Markdown("### Wochenplan erstellen")

                with gr.Row():
                    diet_type = gr.Dropdown(
                        choices=["Balanced", "Low-Carb", "Keto", "High-Protein"],
                        value="Balanced",
                        label="Ernährungstyp",
                        scale=1
                    )
                    calories = gr.Slider(
                        minimum=1200,
                        maximum=3500,
                        value=2000,
                        step=100,
                        label="Kalorien/Tag",
                        scale=2
                    )

                preferences = gr.Textbox(
                    label="Präferenzen/Einschränkungen",
                    placeholder="z.B. Keine Nüsse, vegetarisch, mag kein Brokkoli...",
                    lines=2
                )

                plan_btn = gr.Button("Wochenplan erstellen", variant="primary", size="lg")

                meal_plan_output = gr.Markdown(label="Wochenplan")
                plan_status = gr.Textbox(label="Status", interactive=False)

            # Tab 3: Recipes
            with gr.Tab("Rezepte"):
                gr.Markdown("### Rezept erstellen")

                with gr.Row():
                    dish_name = gr.Textbox(
                        label="Gericht",
                        placeholder="z.B. Hähnchen Curry, Salat, Omelette...",
                        scale=2
                    )
                    recipe_diet = gr.Dropdown(
                        choices=["Balanced", "Low-Carb", "Keto", "High-Protein"],
                        value="Balanced",
                        label="Ernährungstyp",
                        scale=1
                    )

                ingredients_input = gr.Textbox(
                    label="Verfügbare Zutaten (optional)",
                    placeholder="z.B. Hähnchen, Paprika, Reis... (kommagetrennt)",
                    lines=2
                )

                max_time = gr.Slider(
                    minimum=10,
                    maximum=120,
                    value=30,
                    step=5,
                    label="Max. Zubereitungszeit (Min)"
                )

                recipe_btn = gr.Button("Rezept erstellen", variant="primary", size="lg")

                recipe_output = gr.Markdown(label="Rezept")
                recipe_status = gr.Textbox(label="Status", interactive=False)

            # Tab 4: Nutrition Analysis
            with gr.Tab("Analyse"):
                gr.Markdown("### Nährwert-Analyse")

                meal_description = gr.Textbox(
                    label="Mahlzeit beschreiben",
                    placeholder="z.B. 2 Scheiben Vollkornbrot mit Käse und Tomaten, 1 Glas Milch...",
                    lines=3
                )

                analyze_btn = gr.Button("Analysieren", variant="primary", size="lg")

                analysis_output = gr.Markdown(label="Analyse")
                analysis_status = gr.Textbox(label="Status", interactive=False)

        # Footer
        gr.Markdown("""
        ---
        **Tipps:**
        - Produkte aus Lidl und Aldi mit Yuka-Score für Gesundheitsbewertung
        - Wochenplan basiert auf echten Produktdaten
        - Low-Carb/Keto optimiert für max. 20g Kohlenhydrate
        """)

        # Event handlers
        connect_btn.click(
            fn=init_clients,
            inputs=[model_select],
            outputs=[connection_status]
        )

        search_btn.click(
            fn=search_products,
            inputs=[search_query, search_store, search_category],
            outputs=[search_results, search_status]
        )

        healthy_btn.click(
            fn=get_healthy_products,
            inputs=[search_store, search_category],
            outputs=[search_results, search_status]
        )

        favorites_btn.click(
            fn=get_favorites,
            outputs=[search_results, search_status]
        )

        plan_btn.click(
            fn=create_meal_plan,
            inputs=[diet_type, calories, preferences, model_select],
            outputs=[meal_plan_output, plan_status]
        )

        recipe_btn.click(
            fn=create_recipe,
            inputs=[dish_name, ingredients_input, recipe_diet, max_time, model_select],
            outputs=[recipe_output, recipe_status]
        )

        analyze_btn.click(
            fn=analyze_nutrition,
            inputs=[meal_description, model_select],
            outputs=[analysis_output, analysis_status]
        )

    return app


# ============== Main ==============

def main():
    """Launch the Gradio app."""
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port from diagram agent
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
