"""
Food API Client

Handles communication with the Food API endpoints.
"""

import os
import requests
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from package directory
_package_dir = Path(__file__).parent
_env_file = _package_dir / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()  # Fallback to current directory


@dataclass
class Product:
    """Food product data."""
    barcode: str
    name: str
    brand: Optional[str] = None
    store: Optional[str] = None
    category: Optional[str] = None
    yuka_score: Optional[int] = None
    nutriscore: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    salt: Optional[float] = None
    is_favorite: bool = False
    image_url: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "Product":
        """Create Product from API response."""
        import json

        # Parse nutritional data if it's a JSON string
        nutritional_data = data.get("nutritional_data", {})
        if isinstance(nutritional_data, str):
            try:
                nutritional_data = json.loads(nutritional_data)
            except (json.JSONDecodeError, TypeError):
                nutritional_data = {}

        # Extract nutrition values with fallbacks
        calories = data.get("calories") or nutritional_data.get("energy-kcal_100g") or nutritional_data.get("energy-kcal")
        protein = data.get("protein") or nutritional_data.get("proteins_100g") or nutritional_data.get("proteins")
        carbs = data.get("carbs") or nutritional_data.get("carbohydrates_100g") or nutritional_data.get("carbohydrates")
        fat = data.get("fat") or nutritional_data.get("fat_100g") or nutritional_data.get("fat")
        fiber = data.get("fiber") or nutritional_data.get("fiber_100g") or nutritional_data.get("fiber")
        sugar = data.get("sugar") or nutritional_data.get("sugars_100g") or nutritional_data.get("sugars")
        salt = data.get("salt") or nutritional_data.get("salt_100g") or nutritional_data.get("salt")

        return cls(
            barcode=data.get("barcode", ""),
            name=data.get("name", data.get("product_name", "")),
            brand=data.get("brand", data.get("brands", "")),
            store=data.get("store", data.get("stores", "")),
            category=data.get("category", data.get("category_key", "")),
            yuka_score=data.get("yuka_score", data.get("score")),
            nutriscore=data.get("nutriscore", data.get("nutriscore_grade")),
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            salt=salt,
            is_favorite=data.get("is_favorite", data.get("isFavorite", False)),
            image_url=data.get("image_url", data.get("image")),
        )

    def nutrition_summary(self) -> str:
        """Get nutrition summary string."""
        parts = []
        if self.calories:
            parts.append(f"{self.calories:.0f} kcal")
        if self.protein:
            parts.append(f"P:{self.protein:.1f}g")
        if self.carbs:
            parts.append(f"C:{self.carbs:.1f}g")
        if self.fat:
            parts.append(f"F:{self.fat:.1f}g")
        return " | ".join(parts) if parts else "Keine Nährwertdaten"


@dataclass
class Category:
    """Food category."""
    name: str
    products: List[Product] = field(default_factory=list)
    count: int = 0


class FoodAPIClient:
    """
    Client for the Food API.

    Handles authentication and provides methods for all API endpoints.
    """

    def __init__(
        self,
        base_url: str = "https://kanban.niclasedge.com",
        username: str = None,
        password: str = None
    ):
        """
        Initialize the API client.

        Args:
            base_url: API base URL
            username: Auth username (defaults to AUTH_USER env var)
            password: Auth password (defaults to AUTH_PASS env var)
        """
        self.base_url = base_url.rstrip("/")
        self.username = username or os.getenv("AUTH_USER", "")
        self.password = password or os.getenv("AUTH_PASS", "")
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def search(self, query: str = None, store: str = None) -> List[Product]:
        """
        Search for products.

        Args:
            query: Search query
            store: Filter by store (Lidl, Aldi-sud)

        Returns:
            List of matching products
        """
        params = {}
        if query:
            params["q"] = query
        if store:
            params["store"] = store

        data = self._request("GET", "/api/food/search", params=params)
        products = data if isinstance(data, list) else data.get("products", [])
        return [Product.from_api(p) for p in products]

    def get_product(self, barcode: str) -> Optional[Product]:
        """
        Get product by barcode.

        Args:
            barcode: Product barcode

        Returns:
            Product or None if not found
        """
        try:
            data = self._request("GET", f"/api/food/product/{barcode}")
            return Product.from_api(data)
        except requests.HTTPError:
            return None

    def get_store_products(
        self,
        store: str,
        category: str = None,
        sort: str = "score",
        limit: int = 100,
        offset: int = 0
    ) -> List[Product]:
        """
        Get products from a specific store.

        Args:
            store: Store name (Lidl, Aldi-sud)
            category: Filter by category
            sort: Sort by (score, name, updated)
            limit: Max results (1-500)
            offset: Pagination offset

        Returns:
            List of products
        """
        params = {"sort": sort, "limit": limit, "offset": offset}
        if category:
            params["category"] = category

        data = self._request("GET", f"/api/food/store/{store}", params=params)
        products = data if isinstance(data, list) else data.get("products", [])
        return [Product.from_api(p) for p in products]

    def get_categories(self, category: str = None) -> List[Category]:
        """
        Get all categories or products in a specific category.

        Args:
            category: Optional category name to filter

        Returns:
            List of categories with products
        """
        params = {}
        if category:
            params["category"] = category

        data = self._request("GET", "/api/food/categories", params=params)

        if isinstance(data, list):
            # List of products in category
            return [Category(
                name=category or "Alle",
                products=[Product.from_api(p) for p in data],
                count=len(data)
            )]
        else:
            # Dict of categories
            categories = []
            for name, products in data.items():
                cat = Category(
                    name=name,
                    products=[Product.from_api(p) for p in products],
                    count=len(products)
                )
                categories.append(cat)
            return categories

    def get_favorites(self) -> List[Product]:
        """Get all favorite products."""
        data = self._request("GET", "/api/food/favorites")
        products = data if isinstance(data, list) else data.get("favorites", [])
        return [Product.from_api(p) for p in products]

    def toggle_favorite(self, barcode: str, add: bool = True) -> bool:
        """
        Add or remove a product from favorites.

        Args:
            barcode: Product barcode
            add: True to add, False to remove

        Returns:
            True if successful
        """
        action = "add" if add else "remove"
        try:
            self._request(
                "POST",
                "/api/food/favorites",
                json={"barcode": barcode, "action": action}
            )
            return True
        except requests.HTTPError:
            return False

    def get_healthy_products(
        self,
        store: str = None,
        min_score: int = 70,
        limit: int = 50
    ) -> List[Product]:
        """
        Get products with high Yuka scores.

        Args:
            store: Optional store filter
            min_score: Minimum Yuka score
            limit: Max results

        Returns:
            List of healthy products
        """
        if store:
            products = self.get_store_products(store, sort="score", limit=limit)
        else:
            # Get from both stores
            lidl = self.get_store_products("Lidl", sort="score", limit=limit // 2)
            aldi = self.get_store_products("Aldi-sud", sort="score", limit=limit // 2)
            products = lidl + aldi

        # Filter by score
        return [p for p in products if p.yuka_score and p.yuka_score >= min_score]

    def search_by_nutrition(
        self,
        max_calories: float = None,
        min_protein: float = None,
        max_carbs: float = None,
        max_sugar: float = None,
        store: str = None,
        limit: int = 50
    ) -> List[Product]:
        """
        Search products by nutritional criteria.

        Args:
            max_calories: Maximum calories per 100g
            min_protein: Minimum protein per 100g
            max_carbs: Maximum carbs per 100g
            max_sugar: Maximum sugar per 100g
            store: Optional store filter
            limit: Max results

        Returns:
            Filtered products
        """
        # Get products
        if store:
            products = self.get_store_products(store, limit=500)
        else:
            lidl = self.get_store_products("Lidl", limit=250)
            aldi = self.get_store_products("Aldi-sud", limit=250)
            products = lidl + aldi

        # Filter by criteria
        filtered = []
        for p in products:
            if max_calories and p.calories and p.calories > max_calories:
                continue
            if min_protein and p.protein and p.protein < min_protein:
                continue
            if max_carbs and p.carbs and p.carbs > max_carbs:
                continue
            if max_sugar and p.sugar and p.sugar > max_sugar:
                continue
            filtered.append(p)

        return filtered[:limit]


# ============== Convenience Functions ==============

def get_client() -> FoodAPIClient:
    """Get a configured API client."""
    return FoodAPIClient()


def search_products(query: str, store: str = None) -> List[Product]:
    """Quick search for products."""
    return get_client().search(query, store)


def get_healthy_options(store: str = None, min_score: int = 70) -> List[Product]:
    """Get healthy product options."""
    return get_client().get_healthy_products(store, min_score)
