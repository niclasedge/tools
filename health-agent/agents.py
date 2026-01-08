"""
Health Agent Definitions

Multi-agent system for meal planning and recipe suggestions.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import json

try:
    from .api_client import FoodAPIClient, Product, get_client
except ImportError:
    from api_client import FoodAPIClient, Product, get_client


# ============== Model Configuration ==============

def get_ollama_model(model_name: str = "gemma3:4b") -> LiteLlm:
    """Get an Ollama model via LiteLLM."""
    return LiteLlm(model=f"ollama_chat/{model_name}")


# ============== Data Classes ==============

@dataclass
class Meal:
    """A single meal."""
    name: str
    type: str  # breakfast, lunch, dinner, snack
    products: List[Product] = field(default_factory=list)
    recipe: Optional[str] = None
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0

    def calculate_nutrition(self):
        """Calculate total nutrition from products."""
        self.calories = sum(p.calories or 0 for p in self.products)
        self.protein = sum(p.protein or 0 for p in self.products)
        self.carbs = sum(p.carbs or 0 for p in self.products)
        self.fat = sum(p.fat or 0 for p in self.products)


@dataclass
class DayPlan:
    """Meal plan for a single day."""
    day: str  # Montag, Dienstag, etc.
    breakfast: Optional[Meal] = None
    lunch: Optional[Meal] = None
    dinner: Optional[Meal] = None
    snacks: List[Meal] = field(default_factory=list)

    def total_calories(self) -> float:
        """Get total calories for the day."""
        total = 0
        if self.breakfast:
            total += self.breakfast.calories
        if self.lunch:
            total += self.lunch.calories
        if self.dinner:
            total += self.dinner.calories
        for snack in self.snacks:
            total += snack.calories
        return total


@dataclass
class WeekPlan:
    """Weekly meal plan."""
    days: List[DayPlan] = field(default_factory=list)
    target_calories: float = 2000
    diet_type: str = "balanced"  # keto, low-carb, balanced, high-protein

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "target_calories": self.target_calories,
            "diet_type": self.diet_type,
            "days": [
                {
                    "day": d.day,
                    "breakfast": d.breakfast.name if d.breakfast else None,
                    "lunch": d.lunch.name if d.lunch else None,
                    "dinner": d.dinner.name if d.dinner else None,
                    "snacks": [s.name for s in d.snacks],
                    "total_calories": d.total_calories()
                }
                for d in self.days
            ]
        }


# ============== Tool Functions ==============

def search_products_tool(query: str, store: str = None) -> str:
    """
    Search for food products.

    Args:
        query: Search query (e.g., "Joghurt", "Hähnchen")
        store: Optional store filter (Lidl, Aldi-sud)

    Returns:
        JSON with matching products
    """
    client = get_client()
    products = client.search(query, store)

    result = []
    for p in products[:10]:  # Limit to 10 results
        result.append({
            "name": p.name,
            "brand": p.brand,
            "store": p.store,
            "calories": p.calories,
            "protein": p.protein,
            "carbs": p.carbs,
            "fat": p.fat,
            "yuka_score": p.yuka_score
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_healthy_products_tool(store: str = None, category: str = None) -> str:
    """
    Get healthy products with high Yuka scores.

    Args:
        store: Optional store filter (Lidl, Aldi-sud)
        category: Optional category (dairy, meat, vegetables, etc.)

    Returns:
        JSON with healthy product options
    """
    client = get_client()

    if category:
        products = client.get_store_products(
            store or "Lidl",
            category=category,
            sort="score",
            limit=20
        )
    else:
        products = client.get_healthy_products(store, min_score=70, limit=20)

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "store": p.store,
            "yuka_score": p.yuka_score,
            "calories": p.calories,
            "protein": p.protein,
            "carbs": p.carbs
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_low_carb_products_tool(max_carbs: float = 10, store: str = None) -> str:
    """
    Get low-carb products for keto/low-carb diets.

    Args:
        max_carbs: Maximum carbs per 100g
        store: Optional store filter

    Returns:
        JSON with low-carb products
    """
    client = get_client()
    products = client.search_by_nutrition(max_carbs=max_carbs, store=store, limit=30)

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "store": p.store,
            "carbs": p.carbs,
            "protein": p.protein,
            "fat": p.fat,
            "calories": p.calories
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_high_protein_products_tool(min_protein: float = 15, store: str = None) -> str:
    """
    Get high-protein products.

    Args:
        min_protein: Minimum protein per 100g
        store: Optional store filter

    Returns:
        JSON with high-protein products
    """
    client = get_client()
    products = client.search_by_nutrition(min_protein=min_protein, store=store, limit=30)

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "store": p.store,
            "protein": p.protein,
            "calories": p.calories,
            "carbs": p.carbs
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_favorites_tool() -> str:
    """
    Get user's favorite products.

    Returns:
        JSON with favorite products
    """
    client = get_client()
    products = client.get_favorites()

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "store": p.store,
            "calories": p.calories,
            "protein": p.protein
        })

    return json.dumps(result, indent=2, ensure_ascii=False)


def get_categories_tool() -> str:
    """
    Get available food categories.

    Returns:
        JSON with category names and product counts
    """
    client = get_client()
    categories = client.get_categories()

    result = [{"name": c.name, "count": c.count} for c in categories]
    return json.dumps(result, indent=2, ensure_ascii=False)


# ============== Agent Definitions ==============

MEAL_PLANNER_INSTRUCTION = """Du bist ein Ernährungsberater und Wochenplaner. Deine Aufgabe ist es, gesunde Wochenpläne zu erstellen.

FÄHIGKEITEN:
1. Erstelle ausgewogene Wochenpläne basierend auf:
   - Kalorienziel (Standard: 2000 kcal/Tag)
   - Ernährungstyp (balanced, low-carb, keto, high-protein)
   - Verfügbare Produkte aus Lidl und Aldi

2. Nutze die Tools um passende Produkte zu finden:
   - search_products_tool: Suche nach spezifischen Produkten
   - get_healthy_products_tool: Finde gesunde Optionen
   - get_low_carb_products_tool: Für Low-Carb/Keto
   - get_high_protein_products_tool: Für Muskelaufbau

OUTPUT FORMAT:
Erstelle strukturierte Wochenpläne im Format:

## Wochenplan: [Typ]

### Montag
- **Frühstück**: [Mahlzeit] (~X kcal)
- **Mittagessen**: [Mahlzeit] (~X kcal)
- **Abendessen**: [Mahlzeit] (~X kcal)
- **Snacks**: [Optional]

[Wiederholen für alle Tage]

### Einkaufsliste
- [ ] Produkt 1 (Store)
- [ ] Produkt 2 (Store)

### Nährwert-Zusammenfassung
- Durchschnittliche Kalorien: X kcal/Tag
- Protein: X g/Tag
- Kohlenhydrate: X g/Tag

Sei kreativ aber realistisch. Nutze echte Produkte aus der Datenbank."""


RECIPE_AGENT_INSTRUCTION = """Du bist ein kreativer Koch und Rezept-Experte. Deine Aufgabe ist es, leckere und gesunde Rezepte zu erstellen.

FÄHIGKEITEN:
1. Erstelle Rezepte basierend auf:
   - Verfügbaren Produkten aus Lidl/Aldi
   - Ernährungszielen (Low-Carb, High-Protein, etc.)
   - Zubereitungszeit
   - Schwierigkeitsgrad

2. Nutze die Tools um Zutaten zu finden:
   - search_products_tool: Suche nach Zutaten
   - get_healthy_products_tool: Finde gesunde Zutaten
   - get_favorites_tool: Nutze Lieblingsprodukte

OUTPUT FORMAT:

## [Rezeptname]

**Schwierigkeit**: Einfach/Mittel/Fortgeschritten
**Zubereitungszeit**: X Minuten
**Portionen**: X

### Zutaten
- X g [Zutat] (Store: Lidl/Aldi)
- X ml [Zutat]
...

### Nährwerte pro Portion
- Kalorien: X kcal
- Protein: X g
- Kohlenhydrate: X g
- Fett: X g

### Zubereitung
1. [Schritt 1]
2. [Schritt 2]
...

### Tipps
- [Variationen]
- [Aufbewahrung]

Erstelle abwechslungsreiche, schmackhafte Rezepte mit echten Produkten."""


NUTRITION_ANALYZER_INSTRUCTION = """Du bist ein Ernährungsanalyst. Deine Aufgabe ist es, Mahlzeiten und Produkte zu analysieren.

FÄHIGKEITEN:
1. Analysiere Nährwerte von Mahlzeiten
2. Berechne Makronährstoffe
3. Gib Empfehlungen für bessere Alternativen
4. Bewerte Produkte nach Gesundheit (Yuka Score)

ANALYSE FORMAT:

## Nährwert-Analyse

### Produkt/Mahlzeit: [Name]

| Nährstoff | Menge | % Tagesbedarf |
|-----------|-------|---------------|
| Kalorien  | X kcal| X%            |
| Protein   | X g   | X%            |
| Kohlenhydrate | X g | X%          |
| Fett      | X g   | X%            |
| Zucker    | X g   | X%            |

### Bewertung
- Yuka Score: X/100
- Nutri-Score: A-E

### Empfehlungen
- [Bessere Alternativen]
- [Tipps zur Optimierung]

Sei präzise und hilfreich in deinen Analysen."""


# ============== Agent Factory Functions ==============

def create_meal_planner_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Meal Planner Agent."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="meal_planner",
        model=model,
        instruction=MEAL_PLANNER_INSTRUCTION,
        description="Erstellt Wochenpläne und Mahlzeitenpläne",
        tools=[
            FunctionTool(search_products_tool),
            FunctionTool(get_healthy_products_tool),
            FunctionTool(get_low_carb_products_tool),
            FunctionTool(get_high_protein_products_tool),
            FunctionTool(get_favorites_tool),
            FunctionTool(get_categories_tool),
        ]
    )


def create_recipe_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Recipe Agent."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="recipe_agent",
        model=model,
        instruction=RECIPE_AGENT_INSTRUCTION,
        description="Erstellt Rezepte basierend auf verfügbaren Produkten",
        tools=[
            FunctionTool(search_products_tool),
            FunctionTool(get_healthy_products_tool),
            FunctionTool(get_favorites_tool),
        ]
    )


def create_nutrition_analyzer_agent(model: LiteLlm = None) -> LlmAgent:
    """Create the Nutrition Analyzer Agent."""
    if model is None:
        model = get_ollama_model()

    return LlmAgent(
        name="nutrition_analyzer",
        model=model,
        instruction=NUTRITION_ANALYZER_INSTRUCTION,
        description="Analysiert Nährwerte und gibt Empfehlungen",
        tools=[
            FunctionTool(search_products_tool),
            FunctionTool(get_healthy_products_tool),
        ]
    )


# Alias for backward compatibility
MealPlannerAgent = create_meal_planner_agent
RecipeAgent = create_recipe_agent


# ============== Agent Registry ==============

class HealthAgentRegistry:
    """Registry for health-related agents."""

    def __init__(self, default_model: str = "gemma3:4b"):
        self.default_model = default_model
        self._agents = {}
        self._model = get_ollama_model(default_model)
        self._register_builtin_agents()

    def _register_builtin_agents(self):
        """Register built-in agents."""
        self.register("meal_planner", create_meal_planner_agent)
        self.register("recipe", create_recipe_agent)
        self.register("nutrition", create_nutrition_analyzer_agent)

    def register(self, name: str, factory_fn):
        """Register an agent factory."""
        self._agents[name] = factory_fn

    def get(self, name: str) -> LlmAgent:
        """Get an agent instance by name."""
        if name not in self._agents:
            raise ValueError(f"Unknown agent: {name}. Available: {list(self._agents.keys())}")
        return self._agents[name](self._model)

    def list_agents(self) -> list:
        """List all registered agent names."""
        return list(self._agents.keys())
