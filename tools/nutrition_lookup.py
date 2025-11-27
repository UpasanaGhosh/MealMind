"""Nutrition lookup tool using USDA FoodData Central API."""
import requests
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from config import config
from utils import get_logger

logger = get_logger(__name__)


class NutritionInfo(BaseModel):
    """Nutrition information for an ingredient."""
    ingredient: str
    amount_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    glycemic_index: Optional[int] = None
    source: str = "USDA FoodData Central"


class NutritionLookupTool:
    """Tool for looking up nutritional information."""
    
    def __init__(self):
        self.api_key = config.USDA_API_KEY
        self.base_url = config.USDA_API_URL
        self.cache: Dict[str, Dict] = {}
    
    def search_food(self, query: str) -> Optional[Dict]:
        """Search for a food item in USDA database.
        
        Args:
            query: Food name to search for
            
        Returns:
            Food data if found, None otherwise
        """
        # Check cache first
        if query.lower() in self.cache:
            logger.info("nutrition_lookup_cache_hit", ingredient=query)
            return self.cache[query.lower()]
        
        if not self.api_key:
            logger.warning("nutrition_lookup_no_api_key", ingredient=query)
            return self._get_fallback_data(query)
        
        try:
            # Search USDA API
            url = f"{self.base_url}/foods/search"
            params = {
                "query": query,
                "api_key": self.api_key,
                "pageSize": 1,
                "dataType": ["Survey (FNDDS)", "Foundation", "SR Legacy"]
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("foods"):
                food_data = data["foods"][0]
                self.cache[query.lower()] = food_data
                logger.info("nutrition_lookup_success", ingredient=query)
                return food_data
            
            logger.warning("nutrition_lookup_not_found", ingredient=query)
            return self._get_fallback_data(query)
            
        except Exception as e:
            logger.error("nutrition_lookup_error", ingredient=query, error=str(e))
            return self._get_fallback_data(query)
    
    def _get_fallback_data(self, ingredient: str) -> Dict:
        """Get fallback nutritional data for common ingredients.
        
        Args:
            ingredient: Ingredient name
            
        Returns:
            Estimated nutritional data
        """
        # Common ingredient estimates (per 100g)
        fallback_db = {
            "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
            "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6},
            "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0},
            "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
            "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0},
            "tomato": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2},
            "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2},
            "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.1},
            "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0},
        }
        
        # Find closest match
        ingredient_lower = ingredient.lower()
        for key, data in fallback_db.items():
            if key in ingredient_lower or ingredient_lower in key:
                logger.info("nutrition_lookup_fallback", ingredient=ingredient, matched=key)
                return {
                    "description": ingredient,
                    "foodNutrients": [
                        {"nutrientName": "Energy", "value": data["calories"], "unitName": "kcal"},
                        {"nutrientName": "Protein", "value": data["protein"], "unitName": "g"},
                        {"nutrientName": "Carbohydrate", "value": data["carbs"], "unitName": "g"},
                        {"nutrientName": "Total lipid (fat)", "value": data["fat"], "unitName": "g"},
                        {"nutrientName": "Fiber", "value": data["fiber"], "unitName": "g"},
                    ]
                }
        
        # Generic default
        logger.info("nutrition_lookup_generic_fallback", ingredient=ingredient)
        return {
            "description": ingredient,
            "foodNutrients": [
                {"nutrientName": "Energy", "value": 100, "unitName": "kcal"},
                {"nutrientName": "Protein", "value": 5, "unitName": "g"},
                {"nutrientName": "Carbohydrate", "value": 15, "unitName": "g"},
                {"nutrientName": "Total lipid (fat)", "value": 3, "unitName": "g"},
                {"nutrientName": "Fiber", "value": 2, "unitName": "g"},
            ]
        }
    
    def lookup(self, ingredient: str, amount_grams: float = 100.0) -> NutritionInfo:
        """Look up nutritional information for an ingredient.
        
        Args:
            ingredient: Name of the ingredient
            amount_grams: Amount in grams (default: 100g)
            
        Returns:
            Nutritional information
        """
        food_data = self.search_food(ingredient)
        
        if not food_data:
            raise ValueError(f"Could not find nutritional data for: {ingredient}")
        
        # Extract nutrients
        nutrients = {n["nutrientName"]: n["value"] for n in food_data.get("foodNutrients", [])}
        
        # Calculate for requested amount (data is per 100g)
        scale = amount_grams / 100.0
        
        return NutritionInfo(
            ingredient=ingredient,
            amount_grams=amount_grams,
            calories=nutrients.get("Energy", 0) * scale,
            protein_g=nutrients.get("Protein", 0) * scale,
            carbs_g=nutrients.get("Carbohydrate, by difference", nutrients.get("Carbohydrate", 0)) * scale,
            fat_g=nutrients.get("Total lipid (fat)", 0) * scale,
            fiber_g=nutrients.get("Fiber, total dietary", nutrients.get("Fiber", 0)) * scale,
            sugar_g=nutrients.get("Sugars, total including NLEA", 0) * scale,
            sodium_mg=nutrients.get("Sodium, Na", 0) * scale,
        )
    
    def batch_lookup(self, ingredients: List[tuple]) -> List[NutritionInfo]:
        """Look up multiple ingredients at once.
        
        Args:
            ingredients: List of (ingredient_name, amount_grams) tuples
            
        Returns:
            List of nutrition info
        """
        results = []
        for ingredient, amount in ingredients:
            try:
                results.append(self.lookup(ingredient, amount))
            except Exception as e:
                logger.error("batch_lookup_error", ingredient=ingredient, error=str(e))
        return results


# Create global instance
nutrition_tool = NutritionLookupTool()


def nutrition_lookup(ingredient: str, amount_grams: float = 100.0) -> Dict:
    """Tool function for nutrition lookup.
    
    This function is decorated as a tool for use with Google ADK agents.
    
    Args:
        ingredient: Name of the ingredient to look up
        amount_grams: Amount in grams (default: 100g)
    
    Returns:
        Dictionary with nutritional information
    """
    result = nutrition_tool.lookup(ingredient, amount_grams)
    return result.model_dump()
