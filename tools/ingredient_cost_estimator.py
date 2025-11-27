"""Ingredient cost estimation tool."""
from typing import Dict, List, Optional
from pydantic import BaseModel
from config import config
from utils import get_logger

logger = get_logger(__name__)


class IngredientCost(BaseModel):
    """Cost information for an ingredient."""
    ingredient: str
    amount_grams: float
    estimated_cost: float
    price_per_kg: float
    category: str


class CostEstimator:
    """Estimate costs for ingredients and recipes."""
    
    def __init__(self):
        """Initialize the cost estimator with default price database."""
        self.price_db = self._load_price_database()
    
    def _load_price_database(self) -> Dict[str, Dict]:
        """Load default price database for common ingredients.
        
        Returns:
            Dictionary mapping ingredient categories to prices per kg
        """
        return {
            # Proteins
            "chicken": {"price_per_kg": config.DEFAULT_PROTEIN_COST, "category": "protein"},
            "beef": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 1.5, "category": "protein"},
            "pork": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 1.2, "category": "protein"},
            "fish": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 1.8, "category": "protein"},
            "salmon": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 2.0, "category": "protein"},
            "turkey": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 1.1, "category": "protein"},
            "tofu": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 0.5, "category": "protein"},
            "egg": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 0.8, "category": "protein"},
            "lentils": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 0.3, "category": "protein"},
            "beans": {"price_per_kg": config.DEFAULT_PROTEIN_COST * 0.3, "category": "protein"},
            
            # Vegetables
            "broccoli": {"price_per_kg": config.DEFAULT_VEGETABLE_COST, "category": "vegetable"},
            "spinach": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 1.2, "category": "vegetable"},
            "carrot": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.7, "category": "vegetable"},
            "tomato": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.9, "category": "vegetable"},
            "onion": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.6, "category": "vegetable"},
            "garlic": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 2.0, "category": "vegetable"},
            "bell pepper": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 1.3, "category": "vegetable"},
            "lettuce": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.8, "category": "vegetable"},
            "cucumber": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.9, "category": "vegetable"},
            "zucchini": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 1.0, "category": "vegetable"},
            
            # Grains & Starches
            "rice": {"price_per_kg": config.DEFAULT_GRAIN_COST, "category": "grain"},
            "pasta": {"price_per_kg": config.DEFAULT_GRAIN_COST * 1.1, "category": "grain"},
            "bread": {"price_per_kg": config.DEFAULT_GRAIN_COST * 1.5, "category": "grain"},
            "quinoa": {"price_per_kg": config.DEFAULT_GRAIN_COST * 2.5, "category": "grain"},
            "oats": {"price_per_kg": config.DEFAULT_GRAIN_COST * 0.8, "category": "grain"},
            "potato": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.5, "category": "grain"},
            "sweet potato": {"price_per_kg": config.DEFAULT_VEGETABLE_COST * 0.8, "category": "grain"},
            
            # Dairy
            "milk": {"price_per_kg": config.DEFAULT_DAIRY_COST * 0.5, "category": "dairy"},
            "cheese": {"price_per_kg": config.DEFAULT_DAIRY_COST * 1.5, "category": "dairy"},
            "yogurt": {"price_per_kg": config.DEFAULT_DAIRY_COST * 0.8, "category": "dairy"},
            "butter": {"price_per_kg": config.DEFAULT_DAIRY_COST * 1.2, "category": "dairy"},
            "cream": {"price_per_kg": config.DEFAULT_DAIRY_COST * 1.0, "category": "dairy"},
            
            # Condiments & Oils (per kg, though typically used in smaller amounts)
            "olive oil": {"price_per_kg": 15.0, "category": "oil"},
            "vegetable oil": {"price_per_kg": 8.0, "category": "oil"},
            "soy sauce": {"price_per_kg": 6.0, "category": "condiment"},
            "vinegar": {"price_per_kg": 4.0, "category": "condiment"},
            "honey": {"price_per_kg": 12.0, "category": "condiment"},
            
            # Spices & Herbs (expensive per kg but used in tiny amounts)
            "salt": {"price_per_kg": 2.0, "category": "spice"},
            "pepper": {"price_per_kg": 20.0, "category": "spice"},
            "cumin": {"price_per_kg": 25.0, "category": "spice"},
            "paprika": {"price_per_kg": 22.0, "category": "spice"},
            "basil": {"price_per_kg": 30.0, "category": "herb"},
            "oregano": {"price_per_kg": 28.0, "category": "herb"},
        }
    
    def _find_ingredient_price(self, ingredient: str) -> tuple:
        """Find the price for an ingredient.
        
        Args:
            ingredient: Ingredient name
            
        Returns:
            Tuple of (price_per_kg, category)
        """
        ingredient_lower = ingredient.lower()
        
        # Direct match
        if ingredient_lower in self.price_db:
            data = self.price_db[ingredient_lower]
            return data["price_per_kg"], data["category"]
        
        # Partial match
        for key, data in self.price_db.items():
            if key in ingredient_lower or ingredient_lower in key:
                logger.info("ingredient_cost_partial_match", ingredient=ingredient, matched=key)
                return data["price_per_kg"], data["category"]
        
        # Default by category guess
        if any(word in ingredient_lower for word in ["meat", "chicken", "beef", "pork", "fish"]):
            return config.DEFAULT_PROTEIN_COST, "protein"
        elif any(word in ingredient_lower for word in ["vegetable", "veggie", "green"]):
            return config.DEFAULT_VEGETABLE_COST, "vegetable"
        elif any(word in ingredient_lower for word in ["rice", "pasta", "bread", "grain"]):
            return config.DEFAULT_GRAIN_COST, "grain"
        elif any(word in ingredient_lower for word in ["milk", "cheese", "dairy", "yogurt"]):
            return config.DEFAULT_DAIRY_COST, "dairy"
        
        # Generic default
        logger.warning("ingredient_cost_generic_default", ingredient=ingredient)
        return 10.0, "unknown"
    
    def estimate_ingredient_cost(
        self,
        ingredient: str,
        amount_grams: float
    ) -> IngredientCost:
        """Estimate the cost of an ingredient.
        
        Args:
            ingredient: Ingredient name
            amount_grams: Amount in grams
            
        Returns:
            Cost information
        """
        price_per_kg, category = self._find_ingredient_price(ingredient)
        amount_kg = amount_grams / 1000.0
        estimated_cost = price_per_kg * amount_kg
        
        logger.info(
            "ingredient_cost_estimated",
            ingredient=ingredient,
            amount_grams=amount_grams,
            cost=estimated_cost
        )
        
        return IngredientCost(
            ingredient=ingredient,
            amount_grams=amount_grams,
            estimated_cost=round(estimated_cost, 2),
            price_per_kg=price_per_kg,
            category=category
        )
    
    def estimate_recipe_cost(
        self,
        ingredients: List[tuple]
    ) -> Dict:
        """Estimate the total cost of a recipe.
        
        Args:
            ingredients: List of (ingredient_name, amount_grams) tuples
            
        Returns:
            Dictionary with cost breakdown and total
        """
        ingredient_costs = []
        total_cost = 0.0
        category_costs = {}
        
        for ingredient, amount in ingredients:
            cost_info = self.estimate_ingredient_cost(ingredient, amount)
            ingredient_costs.append(cost_info.model_dump())
            total_cost += cost_info.estimated_cost
            
            category = cost_info.category
            category_costs[category] = category_costs.get(category, 0.0) + cost_info.estimated_cost
        
        return {
            "ingredients": ingredient_costs,
            "total_cost": round(total_cost, 2),
            "category_breakdown": {k: round(v, 2) for k, v in category_costs.items()},
            "currency": "USD"
        }
    
    def estimate_weekly_cost(
        self,
        daily_meals: List[List[tuple]]
    ) -> Dict:
        """Estimate the cost for a week of meals.
        
        Args:
            daily_meals: List of 7 days, each containing list of meal ingredients
            
        Returns:
            Dictionary with weekly cost breakdown
        """
        daily_costs = []
        total_weekly_cost = 0.0
        
        for day_idx, meals in enumerate(daily_meals, 1):
            day_total = 0.0
            for meal_ingredients in meals:
                recipe_cost = self.estimate_recipe_cost(meal_ingredients)
                day_total += recipe_cost["total_cost"]
            
            daily_costs.append({
                "day": day_idx,
                "cost": round(day_total, 2)
            })
            total_weekly_cost += day_total
        
        return {
            "daily_costs": daily_costs,
            "weekly_total": round(total_weekly_cost, 2),
            "average_per_day": round(total_weekly_cost / 7, 2),
            "currency": "USD"
        }


# Create global instance
cost_estimator = CostEstimator()


# Tool functions for agent use
def estimate_ingredient_cost(ingredient: str, amount_grams: float) -> Dict:
    """Estimate the cost of a single ingredient.
    
    Args:
        ingredient: Name of the ingredient
        amount_grams: Amount in grams
    
    Returns:
        Dictionary with cost information
    """
    result = cost_estimator.estimate_ingredient_cost(ingredient, amount_grams)
    return result.model_dump()


def estimate_recipe_cost(ingredients: List[Dict]) -> Dict:
    """Estimate the total cost of a recipe.
    
    Args:
        ingredients: List of dicts with 'name' and 'amount_grams' keys
    
    Returns:
        Dictionary with cost breakdown
    """
    ingredient_tuples = [(item["name"], item["amount_grams"]) for item in ingredients]
    return cost_estimator.estimate_recipe_cost(ingredient_tuples)


def estimate_weekly_cost(weekly_meals: List[List[List[Dict]]]) -> Dict:
    """Estimate the cost for a week of meals.
    
    Args:
        weekly_meals: List of 7 days, each with meals, each meal with ingredients
    
    Returns:
        Dictionary with weekly cost breakdown
    """
    daily_meals = []
    for day in weekly_meals:
        day_ingredient_lists = []
        for meal in day:
            meal_tuples = [(item["name"], item["amount_grams"]) for item in meal]
            day_ingredient_lists.append(meal_tuples)
        daily_meals.append(day_ingredient_lists)
    
    return cost_estimator.estimate_weekly_cost(daily_meals)
