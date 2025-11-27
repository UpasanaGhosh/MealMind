"""Nutrition Compliance Agent - Validates recipes against nutritional requirements."""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from tools import nutrition_tool
from utils import get_logger

logger = get_logger(__name__)


class NutritionValidationResult(BaseModel):
    """Result of nutrition validation."""
    is_compliant: bool
    violations: List[str] = []
    warnings: List[str] = []
    nutritional_summary: Dict[str, float] = {}
    recommendations: List[str] = []


class NutritionComplianceAgent:
    """Agent responsible for validating recipes against nutritional requirements."""
    
    def __init__(self):
        """Initialize the Nutrition Compliance Agent."""
        self.nutrition_tool = nutrition_tool
        logger.info("nutrition_compliance_agent_initialized")
    
    def calculate_recipe_nutrition(self, recipe: Dict) -> Dict[str, float]:
        """Calculate total nutritional values for a recipe.
        
        Args:
            recipe: Recipe dictionary with ingredients
            
        Returns:
            Dictionary with total nutritional values
        """
        total_nutrition = {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "sodium_mg": 0.0
        }
        
        for ingredient in recipe.get("ingredients", []):
            try:
                # Convert amount to grams if needed
                amount_grams = ingredient.get("amount", 0)
                if ingredient.get("unit") == "ml":
                    # Approximate: 1 ml ≈ 1 gram for most liquids
                    amount_grams = amount_grams
                elif ingredient.get("unit") == "pieces":
                    # Skip pieces, hard to estimate
                    continue
                
                nutrition = self.nutrition_tool.lookup(
                    ingredient["name"],
                    amount_grams
                )
                
                total_nutrition["calories"] += nutrition.calories
                total_nutrition["protein_g"] += nutrition.protein_g
                total_nutrition["carbs_g"] += nutrition.carbs_g
                total_nutrition["fat_g"] += nutrition.fat_g
                total_nutrition["fiber_g"] += nutrition.fiber_g
                total_nutrition["sugar_g"] += nutrition.sugar_g
                total_nutrition["sodium_mg"] += nutrition.sodium_mg
                
            except Exception as e:
                logger.warning(
                    "nutrition_calculation_error",
                    ingredient=ingredient.get("name"),
                    error=str(e)
                )
        
        # Calculate per serving
        servings = recipe.get("servings", 4)
        per_serving = {
            key: round(value / servings, 2)
            for key, value in total_nutrition.items()
        }
        
        logger.info(
            "recipe_nutrition_calculated",
            recipe=recipe.get("name"),
            calories_per_serving=per_serving["calories"]
        )
        
        return per_serving
    
    def check_allergens(
        self,
        recipe: Dict,
        allergies: List[str]
    ) -> List[str]:
        """Check if recipe contains any allergens.
        
        Args:
            recipe: Recipe dictionary
            allergies: List of allergens to check for
            
        Returns:
            List of found allergens
        """
        found_allergens = []
        
        for ingredient in recipe.get("ingredients", []):
            ingredient_name = ingredient.get("name", "").lower()
            
            for allergen in allergies:
                allergen_lower = allergen.lower()
                if allergen_lower in ingredient_name:
                    found_allergens.append(f"{allergen} (found in {ingredient['name']})")
        
        return found_allergens
    
    def check_dietary_restrictions(
        self,
        recipe: Dict,
        restrictions: List[str]
    ) -> List[str]:
        """Check if recipe violates dietary restrictions.
        
        Args:
            recipe: Recipe dictionary
            restrictions: List of dietary restrictions
            
        Returns:
            List of violations
        """
        violations = []
        
        # Common restriction patterns
        restriction_patterns = {
            "vegan": ["meat", "chicken", "beef", "pork", "fish", "egg", "milk", "cheese", "butter", "cream", "yogurt"],
            "vegetarian": ["meat", "chicken", "beef", "pork", "fish", "salmon"],
            "gluten-free": ["wheat", "bread", "pasta", "flour", "barley", "rye"],
            "dairy-free": ["milk", "cheese", "butter", "cream", "yogurt"],
            "keto": ["rice", "pasta", "bread", "potato", "sugar"],
            "low-carb": ["rice", "pasta", "bread", "potato"],
        }
        
        for restriction in restrictions:
            restriction_lower = restriction.lower()
            if restriction_lower in restriction_patterns:
                forbidden = restriction_patterns[restriction_lower]
                
                for ingredient in recipe.get("ingredients", []):
                    ingredient_name = ingredient.get("name", "").lower()
                    
                    for forbidden_item in forbidden:
                        if forbidden_item in ingredient_name:
                            violations.append(
                                f"{restriction} restriction violated: contains {ingredient['name']}"
                            )
                            break
        
        return violations
    
    def check_health_conditions(
        self,
        recipe: Dict,
        health_conditions: List[str],
        health_guidelines: Dict
    ) -> Tuple[List[str], List[str]]:
        """Check if recipe is suitable for health conditions.
        
        Args:
            recipe: Recipe dictionary
            health_conditions: List of health conditions
            health_guidelines: Guidelines for each condition
            
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        for condition in health_conditions:
            guidelines = health_guidelines.get(condition.lower(), {})
            avoid = guidelines.get("avoid", [])
            prefer = guidelines.get("prefer", [])
            
            # Check for items to avoid
            for ingredient in recipe.get("ingredients", []):
                ingredient_name = ingredient.get("name", "").lower()
                
                for avoid_item in avoid:
                    if avoid_item.lower() in ingredient_name:
                        violations.append(
                            f"{condition}: should avoid {ingredient['name']}"
                        )
            
            # Check for preferred items (warnings if missing many)
            has_preferred = False
            for ingredient in recipe.get("ingredients", []):
                ingredient_name = ingredient.get("name", "").lower()
                for prefer_item in prefer:
                    if prefer_item.lower() in ingredient_name:
                        has_preferred = True
                        break
                if has_preferred:
                    break
            
            if not has_preferred and prefer:
                warnings.append(
                    f"{condition}: consider adding {', '.join(prefer[:3])}"
                )
        
        return violations, warnings
    
    def check_calorie_targets(
        self,
        nutrition_per_serving: Dict[str, float],
        members: List[Dict],
        meal_type: str
    ) -> List[str]:
        """Check if recipe meets calorie targets.
        
        Args:
            nutrition_per_serving: Nutritional values per serving
            members: List of family members with calorie targets
            meal_type: Type of meal (breakfast, lunch, dinner)
            
        Returns:
            List of warnings
        """
        warnings = []
        
        # Estimate meal percentage of daily calories
        meal_percentages = {
            "breakfast": 0.25,
            "lunch": 0.35,
            "dinner": 0.40
        }
        meal_pct = meal_percentages.get(meal_type, 0.33)
        
        calories = nutrition_per_serving.get("calories", 0)
        
        for member in members:
            target = member.get("calorie_target")
            if target:
                expected_calories = target * meal_pct
                difference = abs(calories - expected_calories)
                
                if difference > expected_calories * 0.3:  # More than 30% off
                    if calories > expected_calories:
                        warnings.append(
                            f"{member['name']}: {meal_type} is {int(calories - expected_calories)} "
                            f"calories over target ({int(expected_calories)} expected)"
                        )
                    else:
                        warnings.append(
                            f"{member['name']}: {meal_type} is {int(expected_calories - calories)} "
                            f"calories under target ({int(expected_calories)} expected)"
                        )
        
        return warnings
    
    def validate_recipe(
        self,
        recipe: Dict,
        planning_context: Dict,
        constraints: Dict
    ) -> NutritionValidationResult:
        """Validate a recipe against all nutritional requirements.
        
        Args:
            recipe: Recipe to validate
            planning_context: Household planning context
            constraints: Dietary constraints
            
        Returns:
            Validation result with compliance status and details
        """
        logger.info(
            "validating_recipe",
            recipe=recipe.get("name"),
            household=planning_context.get("household_id")
        )
        
        violations = []
        warnings = []
        recommendations = []
        
        # Calculate nutrition
        nutrition = self.calculate_recipe_nutrition(recipe)
        
        # Check allergens (CRITICAL)
        allergens = constraints.get("allergies", [])
        if allergens:
            found = self.check_allergens(recipe, allergens)
            if found:
                violations.extend([f"ALLERGEN ALERT: {a}" for a in found])
        
        # Check dietary restrictions
        restrictions = constraints.get("dietary_restrictions", [])
        if restrictions:
            restriction_violations = self.check_dietary_restrictions(recipe, restrictions)
            violations.extend(restriction_violations)
        
        # Check health conditions
        health_conditions = constraints.get("health_conditions", [])
        health_guidelines = constraints.get("health_guidelines", {})
        if health_conditions:
            condition_violations, condition_warnings = self.check_health_conditions(
                recipe, health_conditions, health_guidelines
            )
            violations.extend(condition_violations)
            warnings.extend(condition_warnings)
        
        # Check calorie targets
        members = planning_context.get("members", [])
        calorie_warnings = self.check_calorie_targets(
            nutrition,
            members,
            recipe.get("meal_type", "dinner")
        )
        warnings.extend(calorie_warnings)
        
        # Check for balanced nutrition
        if nutrition.get("protein_g", 0) < 15:
            recommendations.append("Consider adding more protein sources")
        
        if nutrition.get("fiber_g", 0) < 5:
            recommendations.append("Consider adding more fiber-rich ingredients")
        
        if nutrition.get("sodium_mg", 0) > 800:
            warnings.append("High sodium content - consider reducing salt")
        
        # Determine compliance
        is_compliant = len(violations) == 0
        
        result = NutritionValidationResult(
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
            nutritional_summary=nutrition,
            recommendations=recommendations
        )
        
        logger.info(
            "recipe_validated",
            recipe=recipe.get("name"),
            compliant=is_compliant,
            violations=len(violations),
            warnings=len(warnings)
        )
        
        return result
    
    def generate_feedback(self, validation_result: NutritionValidationResult) -> str:
        """Generate feedback text for recipe regeneration.
        
        Args:
            validation_result: Validation result
            
        Returns:
            Feedback string for recipe generator
        """
        if validation_result.is_compliant:
            return "Recipe is compliant with all requirements."
        
        feedback_parts = []
        
        if validation_result.violations:
            feedback_parts.append("CRITICAL ISSUES:")
            for violation in validation_result.violations:
                feedback_parts.append(f"  - {violation}")
        
        if validation_result.warnings:
            feedback_parts.append("\nWARNINGS:")
            for warning in validation_result.warnings:
                feedback_parts.append(f"  - {warning}")
        
        if validation_result.recommendations:
            feedback_parts.append("\nRECOMMENDATIONS:")
            for rec in validation_result.recommendations:
                feedback_parts.append(f"  - {rec}")
        
        return "\n".join(feedback_parts)


# Create global instance
nutrition_compliance = NutritionComplianceAgent()
