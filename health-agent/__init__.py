"""
Health Agent - AI-powered meal planning and nutrition assistant.

Features:
- Food database search (Lidl, Aldi)
- Weekly meal planning
- Recipe suggestions based on available products
- Nutritional analysis
"""

from .api_client import FoodAPIClient
from .agents import MealPlannerAgent, RecipeAgent, HealthAgentRegistry
from .orchestrator import HealthOrchestrator

__version__ = "0.1.0"
__all__ = [
    "FoodAPIClient",
    "MealPlannerAgent",
    "RecipeAgent",
    "HealthAgentRegistry",
    "HealthOrchestrator",
]
