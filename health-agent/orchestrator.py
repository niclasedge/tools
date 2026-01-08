"""
Health Agent Orchestrator

Coordinates the multi-agent pipeline for meal planning and recipes.
"""

import time
import litellm
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

try:
    from .agents import HealthAgentRegistry, get_ollama_model
    from .api_client import FoodAPIClient, get_client, Product
except ImportError:
    from agents import HealthAgentRegistry, get_ollama_model
    from api_client import FoodAPIClient, get_client, Product


class TaskType(Enum):
    """Types of health agent tasks."""
    MEAL_PLAN = "meal_plan"
    RECIPE = "recipe"
    NUTRITION = "nutrition"
    SEARCH = "search"


@dataclass
class HealthResult:
    """Result of a health agent task."""
    success: bool
    task_type: TaskType
    content: str
    products: List[Product] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "task_type": self.task_type.value,
            "content": self.content,
            "products": [{"name": p.name, "store": p.store} for p in self.products],
            "errors": self.errors,
            "duration_seconds": self.duration_seconds
        }


class HealthOrchestrator:
    """
    Orchestrates health-related AI tasks.

    Supports:
    - Weekly meal planning
    - Recipe generation
    - Nutrition analysis
    - Product search
    """

    def __init__(
        self,
        model_name: str = "gemma3:4b",
        diet_type: str = "balanced",
        target_calories: int = 2000
    ):
        """
        Initialize the orchestrator.

        Args:
            model_name: Ollama model to use
            diet_type: Diet type (balanced, keto, low-carb, high-protein)
            target_calories: Daily calorie target
        """
        self.model_name = model_name
        self.diet_type = diet_type
        self.target_calories = target_calories
        self.registry = HealthAgentRegistry(default_model=model_name)
        self.api_client = get_client()

    def _run_agent_sync(self, agent_name: str, prompt: str) -> str:
        """Run an agent synchronously using LiteLLM."""
        agent = self.registry.get(agent_name)

        response = litellm.completion(
            model=f"ollama_chat/{self.model_name}",
            messages=[
                {"role": "system", "content": agent.instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    def create_week_plan(
        self,
        preferences: str = "",
        diet_type: str = None,
        target_calories: int = None
    ) -> HealthResult:
        """
        Create a weekly meal plan.

        Args:
            preferences: User preferences (allergies, likes, dislikes)
            diet_type: Override diet type
            target_calories: Override calorie target

        Returns:
            HealthResult with meal plan
        """
        start_time = time.time()

        diet = diet_type or self.diet_type
        calories = target_calories or self.target_calories

        prompt = f"""Erstelle einen kompletten Wochenplan für 7 Tage.

EINSTELLUNGEN:
- Ernährungstyp: {diet}
- Kalorienziel: {calories} kcal/Tag
- Präferenzen: {preferences if preferences else "Keine besonderen Einschränkungen"}

ANFORDERUNGEN:
1. Nutze echte Produkte aus Lidl und Aldi (nutze die Such-Tools)
2. Erstelle abwechslungsreiche Mahlzeiten
3. Berechne ungefähre Nährwerte
4. Erstelle eine Einkaufsliste am Ende

Beginne mit der Produktsuche und erstelle dann den Plan."""

        try:
            content = self._run_agent_sync("meal_planner", prompt)
            return HealthResult(
                success=True,
                task_type=TaskType.MEAL_PLAN,
                content=content,
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return HealthResult(
                success=False,
                task_type=TaskType.MEAL_PLAN,
                content="",
                errors=[str(e)],
                duration_seconds=time.time() - start_time
            )

    def create_recipe(
        self,
        dish_name: str = "",
        ingredients: List[str] = None,
        diet_type: str = None,
        max_time: int = 30
    ) -> HealthResult:
        """
        Create a recipe.

        Args:
            dish_name: Name of dish to create
            ingredients: Available ingredients
            diet_type: Diet restriction
            max_time: Max preparation time in minutes

        Returns:
            HealthResult with recipe
        """
        start_time = time.time()

        diet = diet_type or self.diet_type

        if dish_name:
            request = f"Erstelle ein Rezept für: {dish_name}"
        elif ingredients:
            request = f"Erstelle ein Rezept mit diesen Zutaten: {', '.join(ingredients)}"
        else:
            request = "Erstelle ein schnelles, gesundes Rezept"

        prompt = f"""{request}

ANFORDERUNGEN:
- Ernährungstyp: {diet}
- Maximale Zubereitungszeit: {max_time} Minuten
- Nutze Produkte aus Lidl/Aldi
- Berechne Nährwerte pro Portion

Suche zuerst nach passenden Produkten, dann erstelle das Rezept."""

        try:
            content = self._run_agent_sync("recipe", prompt)
            return HealthResult(
                success=True,
                task_type=TaskType.RECIPE,
                content=content,
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return HealthResult(
                success=False,
                task_type=TaskType.RECIPE,
                content="",
                errors=[str(e)],
                duration_seconds=time.time() - start_time
            )

    def analyze_nutrition(
        self,
        meal_description: str
    ) -> HealthResult:
        """
        Analyze nutrition of a meal or product.

        Args:
            meal_description: Description of meal or product name

        Returns:
            HealthResult with analysis
        """
        start_time = time.time()

        prompt = f"""Analysiere die Nährwerte von: {meal_description}

AUFGABEN:
1. Suche nach den relevanten Produkten
2. Berechne Gesamtnährwerte
3. Vergleiche mit Tagesbedarf
4. Gib Empfehlungen für bessere Alternativen

Nutze die Such-Tools um echte Produktdaten zu finden."""

        try:
            content = self._run_agent_sync("nutrition", prompt)
            return HealthResult(
                success=True,
                task_type=TaskType.NUTRITION,
                content=content,
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return HealthResult(
                success=False,
                task_type=TaskType.NUTRITION,
                content="",
                errors=[str(e)],
                duration_seconds=time.time() - start_time
            )

    def search_products(
        self,
        query: str,
        filters: Dict[str, Any] = None
    ) -> HealthResult:
        """
        Search for products.

        Args:
            query: Search query
            filters: Optional filters (store, category, max_calories, etc.)

        Returns:
            HealthResult with products
        """
        start_time = time.time()
        filters = filters or {}

        try:
            # Direct API search
            store = filters.get("store")
            products = self.api_client.search(query, store)

            # Apply filters
            if filters.get("max_calories"):
                products = [p for p in products if p.calories and p.calories <= filters["max_calories"]]
            if filters.get("min_protein"):
                products = [p for p in products if p.protein and p.protein >= filters["min_protein"]]
            if filters.get("min_score"):
                products = [p for p in products if p.yuka_score and p.yuka_score >= filters["min_score"]]

            # Format results
            content = f"## Suchergebnisse für: {query}\n\n"
            content += f"Gefunden: {len(products)} Produkte\n\n"

            for p in products[:20]:
                content += f"### {p.name}\n"
                content += f"- Store: {p.store}\n"
                content += f"- {p.nutrition_summary()}\n"
                if p.yuka_score:
                    content += f"- Yuka Score: {p.yuka_score}/100\n"
                content += "\n"

            return HealthResult(
                success=True,
                task_type=TaskType.SEARCH,
                content=content,
                products=products[:20],
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return HealthResult(
                success=False,
                task_type=TaskType.SEARCH,
                content="",
                errors=[str(e)],
                duration_seconds=time.time() - start_time
            )


# ============== Convenience Functions ==============

def create_meal_plan(
    diet_type: str = "balanced",
    calories: int = 2000,
    preferences: str = "",
    model: str = "gemma3:4b"
) -> HealthResult:
    """
    Quick function to create a meal plan.

    Args:
        diet_type: Diet type
        calories: Daily calorie target
        preferences: User preferences
        model: Ollama model name

    Returns:
        HealthResult
    """
    orchestrator = HealthOrchestrator(
        model_name=model,
        diet_type=diet_type,
        target_calories=calories
    )
    return orchestrator.create_week_plan(preferences)


def get_recipe(
    dish: str = "",
    ingredients: List[str] = None,
    diet_type: str = "balanced",
    model: str = "gemma3:4b"
) -> HealthResult:
    """
    Quick function to get a recipe.

    Args:
        dish: Dish name
        ingredients: Available ingredients
        diet_type: Diet restriction
        model: Ollama model name

    Returns:
        HealthResult
    """
    orchestrator = HealthOrchestrator(model_name=model, diet_type=diet_type)
    return orchestrator.create_recipe(dish, ingredients)


def analyze_meal(
    description: str,
    model: str = "gemma3:4b"
) -> HealthResult:
    """
    Quick function to analyze a meal.

    Args:
        description: Meal description
        model: Ollama model name

    Returns:
        HealthResult
    """
    orchestrator = HealthOrchestrator(model_name=model)
    return orchestrator.analyze_nutrition(description)
