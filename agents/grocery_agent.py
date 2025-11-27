"""Grocery List Agent - Creates organized shopping lists from meal plans."""
from typing import Dict, List
from collections import defaultdict
from pydantic import BaseModel
from tools import cost_estimator
from utils import get_logger

logger = get_logger(__name__)


class GroceryItem(BaseModel):
    """Grocery list item."""
    name: str
    total_amount: float
    unit: str
    category: str
    estimated_cost: float
    used_in_meals: List[str] = []


class GroceryList(BaseModel):
    """Complete grocery list."""
    items: List[GroceryItem]
    items_by_category: Dict[str, List[GroceryItem]]
    total_items: int
    total_estimated_cost: float
    shopping_tips: List[str]


class GroceryListAgent:
    """Agent responsible for creating organized grocery lists."""
    
    def __init__(self):
        """Initialize the Grocery List Agent."""
        self.cost_estimator = cost_estimator
        
        # Category mapping for organization
        self.category_map = {
            # Proteins
            "chicken": "Meat & Poultry",
            "beef": "Meat & Poultry",
            "pork": "Meat & Poultry",
            "turkey": "Meat & Poultry",
            "fish": "Seafood",
            "salmon": "Seafood",
            "shrimp": "Seafood",
            "tofu": "Meat Alternatives",
            "egg": "Dairy & Eggs",
            
            # Dairy
            "milk": "Dairy & Eggs",
            "cheese": "Dairy & Eggs",
            "yogurt": "Dairy & Eggs",
            "butter": "Dairy & Eggs",
            "cream": "Dairy & Eggs",
            
            # Vegetables
            "broccoli": "Vegetables",
            "carrot": "Vegetables",
            "spinach": "Vegetables",
            "tomato": "Vegetables",
            "onion": "Vegetables",
            "garlic": "Vegetables",
            "bell pepper": "Vegetables",
            "lettuce": "Vegetables",
            "cucumber": "Vegetables",
            "zucchini": "Vegetables",
            "potato": "Vegetables",
            "sweet potato": "Vegetables",
            
            # Grains
            "rice": "Grains & Pasta",
            "pasta": "Grains & Pasta",
            "bread": "Bakery",
            "quinoa": "Grains & Pasta",
            "oats": "Grains & Pasta",
            
            # Condiments & Oils
            "olive oil": "Oils & Condiments",
            "vegetable oil": "Oils & Condiments",
            "soy sauce": "Oils & Condiments",
            "vinegar": "Oils & Condiments",
            "honey": "Oils & Condiments",
            
            # Spices
            "salt": "Spices & Herbs",
            "pepper": "Spices & Herbs",
            "cumin": "Spices & Herbs",
            "paprika": "Spices & Herbs",
            "basil": "Spices & Herbs",
            "oregano": "Spices & Herbs",
            
            # Fruits
            "lemon": "Fruits",
            "apple": "Fruits",
            "banana": "Fruits",
        }
        
        logger.info("grocery_list_agent_initialized")
    
    def categorize_ingredient(self, ingredient_name: str) -> str:
        """Categorize an ingredient.
        
        Args:
            ingredient_name: Name of the ingredient
            
        Returns:
            Category name
        """
        ingredient_lower = ingredient_name.lower()
        
        # Check direct mapping
        for key, category in self.category_map.items():
            if key in ingredient_lower:
                return category
        
        # Default categories based on keywords
        if any(word in ingredient_lower for word in ["meat", "chicken", "beef", "pork"]):
            return "Meat & Poultry"
        elif any(word in ingredient_lower for word in ["fish", "seafood", "salmon"]):
            return "Seafood"
        elif any(word in ingredient_lower for word in ["vegetable", "veggie"]):
            return "Vegetables"
        elif any(word in ingredient_lower for word in ["fruit"]):
            return "Fruits"
        elif any(word in ingredient_lower for word in ["milk", "cheese", "dairy"]):
            return "Dairy & Eggs"
        elif any(word in ingredient_lower for word in ["rice", "pasta", "grain"]):
            return "Grains & Pasta"
        elif any(word in ingredient_lower for word in ["spice", "herb", "seasoning"]):
            return "Spices & Herbs"
        
        return "Other"
    
    def aggregate_ingredients(self, weekly_plan: List[Dict]) -> Dict[str, Dict]:
        """Aggregate ingredients from weekly meal plan.
        
        Args:
            weekly_plan: List of daily meal plans
            
        Returns:
            Dictionary mapping ingredient names to aggregated data
        """
        aggregated = defaultdict(lambda: {
            "total_amount": 0.0,
            "unit": "",
            "meals": []
        })
        
        for day in weekly_plan:
            day_num = day.get("day", 0)
            for meal in day.get("meals", []):
                meal_name = meal.get("name", "")
                meal_label = f"Day {day_num} - {meal_name}"
                
                for ingredient in meal.get("ingredients", []):
                    name = ingredient.get("name", "").lower()
                    amount = ingredient.get("amount", 0)
                    unit = ingredient.get("unit", "")
                    
                    # Convert to consistent units (grams)
                    if unit == "ml":
                        # Approximate: 1 ml ≈ 1 gram for most liquids
                        amount_in_grams = amount
                    elif unit == "pieces":
                        # Skip aggregation for pieces, list separately
                        amount_in_grams = 0
                    else:
                        amount_in_grams = amount
                    
                    if amount_in_grams > 0:
                        aggregated[name]["total_amount"] += amount_in_grams
                        aggregated[name]["unit"] = "grams"
                    else:
                        # For pieces, just count occurrences
                        if not aggregated[name]["unit"]:
                            aggregated[name]["unit"] = unit
                            aggregated[name]["total_amount"] = amount
                        else:
                            aggregated[name]["total_amount"] += amount
                    
                    aggregated[name]["meals"].append(meal_label)
        
        return dict(aggregated)
    
    def create_grocery_list(
        self,
        weekly_plan: List[Dict],
        budget: float = None
    ) -> GroceryList:
        """Create a complete grocery list from weekly meal plan.
        
        Args:
            weekly_plan: List of daily meal plans
            budget: Optional weekly budget
            
        Returns:
            Organized grocery list with categories and costs
        """
        logger.info("creating_grocery_list", days=len(weekly_plan))
        
        # Aggregate ingredients
        aggregated = self.aggregate_ingredients(weekly_plan)
        
        # Create grocery items with cost estimates
        grocery_items = []
        
        for ingredient_name, data in aggregated.items():
            # Estimate cost
            cost_info = self.cost_estimator.estimate_ingredient_cost(
                ingredient_name,
                data["total_amount"]
            )
            
            # Categorize
            category = self.categorize_ingredient(ingredient_name)
            
            item = GroceryItem(
                name=ingredient_name.title(),
                total_amount=round(data["total_amount"], 1),
                unit=data["unit"],
                category=category,
                estimated_cost=cost_info.estimated_cost,
                used_in_meals=data["meals"]
            )
            
            grocery_items.append(item)
        
        # Sort by category, then by name
        grocery_items.sort(key=lambda x: (x.category, x.name))
        
        # Group by category
        items_by_category = defaultdict(list)
        for item in grocery_items:
            items_by_category[item.category].append(item)
        
        # Calculate total cost
        total_cost = sum(item.estimated_cost for item in grocery_items)
        
        # Generate shopping tips
        tips = self._generate_shopping_tips(
            grocery_items,
            total_cost,
            budget
        )
        
        grocery_list = GroceryList(
            items=grocery_items,
            items_by_category=dict(items_by_category),
            total_items=len(grocery_items),
            total_estimated_cost=round(total_cost, 2),
            shopping_tips=tips
        )
        
        logger.info(
            "grocery_list_created",
            total_items=len(grocery_items),
            total_cost=total_cost,
            categories=len(items_by_category)
        )
        
        return grocery_list
    
    def _generate_shopping_tips(
        self,
        items: List[GroceryItem],
        total_cost: float,
        budget: float = None
    ) -> List[str]:
        """Generate helpful shopping tips.
        
        Args:
            items: List of grocery items
            total_cost: Total estimated cost
            budget: Optional budget constraint
            
        Returns:
            List of shopping tips
        """
        tips = []
        
        # Budget tips
        if budget and total_cost > budget:
            over_budget = total_cost - budget
            tips.append(
                f"⚠️ Estimated cost (${total_cost:.2f}) exceeds budget (${budget:.2f}) "
                f"by ${over_budget:.2f}"
            )
            tips.append(
                "Consider: buying generic brands, using coupons, or adjusting recipes"
            )
        elif budget:
            under_budget = budget - total_cost
            tips.append(
                f"✓ Within budget! You have ${under_budget:.2f} remaining"
            )
        
        # Freshness tips
        fresh_items = [item for item in items 
                      if item.category in ["Vegetables", "Fruits", "Seafood", "Meat & Poultry"]]
        if fresh_items:
            tips.append(
                f"Buy fresh items ({len(fresh_items)} items) closer to when you'll use them"
            )
        
        # Bulk buying tips
        frequent_items = [item for item in items 
                         if len(item.used_in_meals) >= 3]
        if frequent_items:
            bulk_names = [item.name for item in frequent_items[:3]]
            tips.append(
                f"Consider buying in bulk: {', '.join(bulk_names)} (used 3+ times)"
            )
        
        # Storage tips
        tips.append(
            "Store herbs and vegetables properly to extend freshness"
        )
        
        # Cost-saving tips
        expensive_items = sorted(
            items,
            key=lambda x: x.estimated_cost,
            reverse=True
        )[:3]
        
        if expensive_items and expensive_items[0].estimated_cost > 10:
            tips.append(
                f"Most expensive items: {', '.join([item.name for item in expensive_items])}"
            )
        
        return tips
    
    def generate_shopping_checklist(
        self,
        grocery_list: GroceryList
    ) -> str:
        """Generate a formatted shopping checklist.
        
        Args:
            grocery_list: Grocery list to format
            
        Returns:
            Formatted checklist string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("  WEEKLY GROCERY LIST")
        lines.append("=" * 60)
        lines.append("")
        
        # Sort categories for logical shopping order
        category_order = [
            "Vegetables",
            "Fruits",
            "Meat & Poultry",
            "Seafood",
            "Dairy & Eggs",
            "Grains & Pasta",
            "Bakery",
            "Oils & Condiments",
            "Spices & Herbs",
            "Meat Alternatives",
            "Other"
        ]
        
        for category in category_order:
            if category in grocery_list.items_by_category:
                items = grocery_list.items_by_category[category]
                lines.append(f"📦 {category.upper()}")
                lines.append("-" * 60)
                
                for item in items:
                    amount_str = f"{item.total_amount:.0f}" if item.unit == "grams" else str(item.total_amount)
                    lines.append(
                        f"  ☐ {item.name:<30} {amount_str:>6} {item.unit:<8} "
                        f"${item.estimated_cost:>6.2f}"
                    )
                
                lines.append("")
        
        # Summary
        lines.append("=" * 60)
        lines.append(f"TOTAL ITEMS: {grocery_list.total_items}")
        lines.append(f"ESTIMATED COST: ${grocery_list.total_estimated_cost:.2f}")
        lines.append("=" * 60)
        
        # Tips
        if grocery_list.shopping_tips:
            lines.append("")
            lines.append("💡 SHOPPING TIPS:")
            for tip in grocery_list.shopping_tips:
                lines.append(f"   • {tip}")
        
        return "\n".join(lines)


# Create global instance
grocery_agent = GroceryListAgent()
