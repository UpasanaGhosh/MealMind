"""Multi-Agent Orchestrator - Coordinates all agents to generate meal plans."""
from typing import Dict, List, Optional
from agents import (
    profile_manager,
    recipe_generator,
    nutrition_compliance,
    schedule_optimizer,
    grocery_agent
)
from memory import memory_bank
from utils import get_logger

logger = get_logger(__name__)


class MealPlanOrchestrator:
    """Orchestrates multiple agents to create complete meal plans."""
    
    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.profile_manager = profile_manager
        self.recipe_generator = recipe_generator
        self.nutrition_compliance = nutrition_compliance
        self.schedule_optimizer = schedule_optimizer
        self.grocery_agent = grocery_agent
        self.memory = memory_bank
        
        logger.info("meal_plan_orchestrator_initialized")
    
    def generate_complete_meal_plan(
        self,
        household_id: str,
        days: int = 7,
        max_retries: int = 3
    ) -> Dict:
        """Generate a complete meal plan with all components.
        
        This orchestrates all agents in sequence:
        1. Profile Manager - Get household context
        2. Recipe Generator - Generate meals for each day
        3. Nutrition Compliance - Validate each recipe (loop if needed)
        4. Schedule Optimizer - Optimize the weekly schedule
        5. Grocery Agent - Create shopping list
        
        Args:
            household_id: Household identifier
            days: Number of days to plan for
            max_retries: Maximum retries per recipe if validation fails
            
        Returns:
            Complete meal plan with all components
        """
        logger.info(
            "starting_meal_plan_generation",
            household_id=household_id,
            days=days
        )
        
        # Step 1: Get household context
        logger.info("step_1_get_context", household_id=household_id)
        planning_context = self.profile_manager.generate_planning_context(household_id)
        constraints = self.profile_manager.get_all_constraints(household_id)
        
        # Validate profile completeness
        validation = self.profile_manager.validate_profile_completeness(household_id)
        if not validation["valid"]:
            raise ValueError(
                f"Household profile incomplete: {', '.join(validation['errors'])}"
            )
        
        # Step 2 & 3: Generate and validate recipes (with loop)
        logger.info("step_2_3_generate_and_validate", days=days)
        weekly_plan = []
        
        for day_num in range(1, days + 1):
            logger.info("generating_day", day=day_num)
            day_meals = {"day": day_num, "meals": []}
            
            for meal_type in ["breakfast", "lunch", "dinner"]:
                recipe = self._generate_validated_recipe(
                    meal_type,
                    planning_context,
                    constraints,
                    max_retries
                )
                
                if recipe:
                    day_meals["meals"].append(recipe)
                else:
                    logger.warning(
                        "recipe_generation_failed",
                        day=day_num,
                        meal_type=meal_type
                    )
            
            weekly_plan.append(day_meals)
        
        # Step 4: Optimize schedule
        logger.info("step_4_optimize_schedule")
        optimization_result = self.schedule_optimizer.optimize_schedule(
            weekly_plan,
            planning_context.get("cooking_time_max", 45)
        )
        
        # Step 5: Create grocery list
        logger.info("step_5_create_grocery_list")
        grocery_list = self.grocery_agent.create_grocery_list(
            weekly_plan,
            planning_context.get("budget_weekly")
        )
        
        # Generate shopping checklist
        shopping_checklist = self.grocery_agent.generate_shopping_checklist(grocery_list)
        
        # Store in memory
        complete_plan = {
            "household_id": household_id,
            "days": days,
            "weekly_plan": weekly_plan,
            "optimization": optimization_result.model_dump(),
            "grocery_list": grocery_list.model_dump(),
            "shopping_checklist": shopping_checklist
        }
        
        self.memory.store_meal_plan(household_id, complete_plan)
        
        logger.info(
            "meal_plan_completed",
            household_id=household_id,
            total_meals=sum(len(day["meals"]) for day in weekly_plan),
            optimization_score=optimization_result.optimization_score,
            grocery_items=grocery_list.total_items,
            total_cost=grocery_list.total_estimated_cost
        )
        
        return complete_plan
    
    def _generate_validated_recipe(
        self,
        meal_type: str,
        planning_context: Dict,
        constraints: Dict,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Generate a recipe and validate it, with retry logic.
        
        Args:
            meal_type: Type of meal
            planning_context: Planning context
            constraints: Constraints
            max_retries: Maximum retry attempts
            
        Returns:
            Validated recipe or None if failed
        """
        for attempt in range(max_retries):
            # Generate recipe
            recipe = self.recipe_generator.generate_recipe(
                meal_type=meal_type,
                planning_context=planning_context,
                constraints=constraints,
                retry_count=attempt
            )
            
            recipe_dict = recipe.model_dump()
            
            # Validate nutrition
            validation = self.nutrition_compliance.validate_recipe(
                recipe_dict,
                planning_context,
                constraints
            )
            
            if validation.is_compliant:
                # Add nutritional info to recipe
                recipe_dict["nutritional_info"] = validation.nutritional_summary
                recipe_dict["nutrition_validated"] = True
                
                logger.info(
                    "recipe_validated_success",
                    recipe=recipe.name,
                    attempt=attempt + 1
                )
                
                return recipe_dict
            else:
                logger.warning(
                    "recipe_validation_failed",
                    recipe=recipe.name,
                    attempt=attempt + 1,
                    violations=len(validation.violations)
                )
                
                if attempt < max_retries - 1:
                    # Generate feedback and retry
                    feedback = self.nutrition_compliance.generate_feedback(validation)
                    logger.info("regenerating_recipe", feedback=feedback[:100])
                    
                    # Use feedback to regenerate
                    recipe = self.recipe_generator.regenerate_recipe(
                        recipe,
                        feedback,
                        planning_context,
                        constraints
                    )
        
        logger.error(
            "recipe_generation_exhausted",
            meal_type=meal_type,
            max_retries=max_retries
        )
        
        return None
    
    def generate_meal_plan_summary(self, meal_plan: Dict) -> str:
        """Generate a human-readable summary of the meal plan.
        
        Args:
            meal_plan: Complete meal plan
            
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("  MEALMIND WEEKLY MEAL PLAN")
        lines.append("=" * 70)
        lines.append(f"\nHousehold: {meal_plan['household_id']}")
        lines.append(f"Days: {meal_plan['days']}")
        lines.append("")
        
        # Weekly schedule
        for day in meal_plan["weekly_plan"]:
            lines.append(f"\n📅 DAY {day['day']}")
            lines.append("-" * 70)
            
            for meal in day["meals"]:
                lines.append(f"\n  {meal['meal_type'].upper()}: {meal['name']}")
                lines.append(f"  Cuisine: {meal['cuisine']} | Time: {meal['cooking_time_minutes']} min")
                
                if meal.get("nutritional_info"):
                    nutrition = meal["nutritional_info"]
                    lines.append(
                        f"  Nutrition: {nutrition['calories']:.0f} cal | "
                        f"P: {nutrition['protein_g']:.0f}g | "
                        f"C: {nutrition['carbs_g']:.0f}g | "
                        f"F: {nutrition['fat_g']:.0f}g"
                    )
        
        # Optimization summary
        optimization = meal_plan["optimization"]
        lines.append("\n" + "=" * 70)
        lines.append("  OPTIMIZATION SUMMARY")
        lines.append("=" * 70)
        
        cooking_stats = optimization["cooking_time_stats"]
        lines.append(f"\n⏱️  Cooking Time:")
        lines.append(f"   Average per day: {cooking_stats['average_per_day']:.0f} minutes")
        lines.append(f"   Total for week: {cooking_stats['total_minutes']:.0f} minutes")
        lines.append(f"   Range: {cooking_stats['min_day']:.0f} - {cooking_stats['max_day']:.0f} minutes")
        
        lines.append(f"\n📊 Optimization Score: {optimization['optimization_score']:.1f}/100")
        
        if optimization["recommendations"]:
            lines.append(f"\n💡 Recommendations:")
            for rec in optimization["recommendations"][:5]:
                lines.append(f"   • {rec}")
        
        # Grocery summary
        grocery = meal_plan["grocery_list"]
        lines.append("\n" + "=" * 70)
        lines.append("  GROCERY LIST SUMMARY")
        lines.append("=" * 70)
        lines.append(f"\nTotal Items: {grocery['total_items']}")
        lines.append(f"Estimated Cost: ${grocery['total_estimated_cost']:.2f}")
        
        lines.append(f"\nCategories:")
        for category, items in grocery["items_by_category"].items():
            lines.append(f"   • {category}: {len(items)} items")
        
        if grocery["shopping_tips"]:
            lines.append(f"\n💡 Shopping Tips:")
            for tip in grocery["shopping_tips"][:3]:
                lines.append(f"   • {tip}")
        
        lines.append("\n" + "=" * 70)
        lines.append("")
        
        return "\n".join(lines)
    
    def quick_plan(
        self,
        household_id: str,
        days: int = 3
    ) -> Dict:
        """Generate a quick meal plan (simplified for demos).
        
        Args:
            household_id: Household identifier
            days: Number of days (default: 3 for quick demo)
            
        Returns:
            Complete meal plan
        """
        logger.info("generating_quick_plan", household_id=household_id, days=days)
        return self.generate_complete_meal_plan(household_id, days, max_retries=2)


# Create global instance
orchestrator = MealPlanOrchestrator()
