"""Schedule Optimizer Agent - Optimizes weekly meal schedule for time and ingredients."""
from typing import Dict, List, Tuple
from collections import defaultdict
from pydantic import BaseModel
from utils import get_logger

logger = get_logger(__name__)


class ScheduleOptimizationResult(BaseModel):
    """Result of schedule optimization."""
    optimized_plan: List[Dict]
    cooking_time_stats: Dict
    ingredient_reuse_stats: Dict[str, int]
    optimization_score: float
    recommendations: List[str]


class ScheduleOptimizerAgent:
    """Agent responsible for optimizing weekly meal schedules."""
    
    def __init__(self):
        """Initialize the Schedule Optimizer Agent."""
        logger.info("schedule_optimizer_agent_initialized")
    
    def analyze_cooking_times(self, weekly_plan: List[Dict]) -> Dict[str, float]:
        """Analyze cooking times across the week.
        
        Args:
            weekly_plan: List of daily meal plans
            
        Returns:
            Dictionary with cooking time statistics
        """
        daily_times = []
        total_time = 0
        max_time = 0
        min_time = float('inf')
        
        for day in weekly_plan:
            day_time = sum(
                meal.get("cooking_time_minutes", 0)
                for meal in day.get("meals", [])
            )
            daily_times.append(day_time)
            total_time += day_time
            max_time = max(max_time, day_time)
            min_time = min(min_time, day_time)
        
        return {
            "total_minutes": total_time,
            "average_per_day": total_time / len(weekly_plan) if weekly_plan else 0,
            "max_day": max_time,
            "min_day": min_time if min_time != float('inf') else 0,
            "daily_times": daily_times
        }
    
    def analyze_ingredient_reuse(self, weekly_plan: List[Dict]) -> Dict[str, int]:
        """Analyze ingredient reuse across the week.
        
        Args:
            weekly_plan: List of daily meal plans
            
        Returns:
            Dictionary mapping ingredient names to usage count
        """
        ingredient_counts = defaultdict(int)
        
        for day in weekly_plan:
            for meal in day.get("meals", []):
                for ingredient in meal.get("ingredients", []):
                    ingredient_name = ingredient.get("name", "").lower()
                    ingredient_counts[ingredient_name] += 1
        
        return dict(ingredient_counts)
    
    def identify_ingredient_clusters(
        self,
        weekly_plan: List[Dict]
    ) -> List[List[str]]:
        """Identify groups of ingredients that are used together.
        
        Args:
            weekly_plan: List of daily meal plans
            
        Returns:
            List of ingredient clusters
        """
        # Track which ingredients appear in the same meals
        co_occurrence = defaultdict(set)
        
        for day in weekly_plan:
            for meal in day.get("meals", []):
                ingredients = [
                    ing.get("name", "").lower()
                    for ing in meal.get("ingredients", [])
                ]
                
                for i, ing1 in enumerate(ingredients):
                    for ing2 in ingredients[i+1:]:
                        co_occurrence[ing1].add(ing2)
                        co_occurrence[ing2].add(ing1)
        
        # Find clusters (simple approach)
        clusters = []
        seen = set()
        
        for ingredient, related in co_occurrence.items():
            if ingredient not in seen and len(related) >= 2:
                cluster = [ingredient] + list(related)[:3]  # Top 3 related
                clusters.append(cluster)
                seen.update(cluster)
        
        return clusters
    
    def optimize_meal_order(
        self,
        weekly_plan: List[Dict],
        cooking_time_max: int = 45
    ) -> List[Dict]:
        """Optimize the order of meals to balance cooking time.
        
        Args:
            weekly_plan: List of daily meal plans
            cooking_time_max: Maximum cooking time per day
            
        Returns:
            Optimized weekly plan
        """
        optimized_plan = []
        
        for day in weekly_plan:
            meals = day.get("meals", [])
            day_num = day.get("day")
            
            # Sort meals by cooking time (longest first)
            sorted_meals = sorted(
                meals,
                key=lambda m: m.get("cooking_time_minutes", 0),
                reverse=True
            )
            
            # Check if total time exceeds limit
            total_time = sum(m.get("cooking_time_minutes", 0) for m in sorted_meals)
            
            optimized_day = {
                "day": day_num,
                "meals": sorted_meals,
                "total_cooking_time": total_time,
                "within_limit": total_time <= cooking_time_max
            }
            
            optimized_plan.append(optimized_day)
        
        return optimized_plan
    
    def suggest_batch_cooking(
        self,
        weekly_plan: List[Dict],
        ingredient_reuse: Dict[str, int]
    ) -> List[str]:
        """Suggest batch cooking opportunities.
        
        Args:
            weekly_plan: List of daily meal plans
            ingredient_reuse: Ingredient usage counts
            
        Returns:
            List of batch cooking suggestions
        """
        suggestions = []
        
        # Find frequently used ingredients
        frequent_ingredients = {
            ing: count for ing, count in ingredient_reuse.items()
            if count >= 3
        }
        
        if frequent_ingredients:
            suggestions.append(
                f"Consider batch cooking: {', '.join(list(frequent_ingredients.keys())[:5])}"
            )
        
        # Find meals with similar base ingredients
        meal_groups = defaultdict(list)
        
        for day_idx, day in enumerate(weekly_plan):
            for meal in day.get("meals", []):
                # Identify base ingredient (protein)
                proteins = ["chicken", "beef", "pork", "fish", "salmon", "tofu"]
                for ing in meal.get("ingredients", []):
                    ing_name = ing.get("name", "").lower()
                    for protein in proteins:
                        if protein in ing_name:
                            meal_groups[protein].append((day_idx + 1, meal.get("name")))
                            break
        
        for protein, meals in meal_groups.items():
            if len(meals) >= 2:
                days = ", ".join([f"Day {day}" for day, _ in meals])
                suggestions.append(
                    f"Batch cook {protein} for {days} to save time"
                )
        
        return suggestions
    
    def suggest_prep_ahead(self, weekly_plan: List[Dict]) -> List[str]:
        """Suggest ingredients that can be prepped ahead.
        
        Args:
            weekly_plan: List of daily meal plans
            
        Returns:
            List of prep-ahead suggestions
        """
        suggestions = []
        
        # Ingredients that can be prepped ahead
        prep_ahead_items = {
            "vegetables": ["onion", "carrot", "bell pepper", "broccoli", "zucchini"],
            "grains": ["rice", "quinoa", "pasta"],
            "proteins": ["chicken", "beef"]
        }
        
        ingredient_usage = defaultdict(list)
        
        for day in weekly_plan:
            day_num = day.get("day")
            for meal in day.get("meals", []):
                for ing in meal.get("ingredients", []):
                    ing_name = ing.get("name", "").lower()
                    ingredient_usage[ing_name].append(day_num)
        
        for category, items in prep_ahead_items.items():
            for item in items:
                days = []
                for ing_name, usage_days in ingredient_usage.items():
                    if item in ing_name and len(usage_days) >= 2:
                        days = usage_days
                        break
                
                if days:
                    suggestions.append(
                        f"Prep {item} ahead for Days {', '.join(map(str, sorted(days)))}"
                    )
        
        return suggestions[:5]  # Limit to top 5
    
    def calculate_optimization_score(
        self,
        cooking_time_stats: Dict[str, float],
        ingredient_reuse: Dict[str, int],
        cooking_time_max: int = 45
    ) -> float:
        """Calculate an optimization score for the meal plan.
        
        Args:
            cooking_time_stats: Cooking time statistics
            ingredient_reuse: Ingredient usage counts
            cooking_time_max: Maximum cooking time per day
            
        Returns:
            Score from 0-100
        """
        score = 100.0
        
        # Penalize if average cooking time exceeds limit
        avg_time = cooking_time_stats.get("average_per_day", 0)
        if avg_time > cooking_time_max:
            time_penalty = ((avg_time - cooking_time_max) / cooking_time_max) * 30
            score -= min(time_penalty, 30)
        
        # Penalize uneven distribution
        max_time = cooking_time_stats.get("max_day", 0)
        min_time = cooking_time_stats.get("min_day", 0)
        if max_time > 0:
            time_variance = (max_time - min_time) / max_time
            if time_variance > 0.5:  # More than 50% variance
                score -= 15
        
        # Reward ingredient reuse
        reused_ingredients = sum(1 for count in ingredient_reuse.values() if count >= 2)
        total_unique = len(ingredient_reuse)
        if total_unique > 0:
            reuse_ratio = reused_ingredients / total_unique
            score += reuse_ratio * 15
        
        return max(0.0, min(100.0, score))
    
    def optimize_schedule(
        self,
        weekly_plan: List[Dict],
        cooking_time_max: int = 45
    ) -> ScheduleOptimizationResult:
        """Optimize the weekly meal schedule.
        
        Args:
            weekly_plan: List of daily meal plans
            cooking_time_max: Maximum cooking time per day
            
        Returns:
            Optimization result with stats and recommendations
        """
        logger.info("optimizing_schedule", days=len(weekly_plan))
        
        # Analyze current state
        cooking_stats = self.analyze_cooking_times(weekly_plan)
        ingredient_reuse = self.analyze_ingredient_reuse(weekly_plan)
        
        # Optimize meal order
        optimized_plan = self.optimize_meal_order(weekly_plan, cooking_time_max)
        
        # Generate recommendations
        recommendations = []
        
        # Time-based recommendations
        if cooking_stats["average_per_day"] > cooking_time_max:
            recommendations.append(
                f"Average cooking time ({cooking_stats['average_per_day']:.0f} min) "
                f"exceeds target ({cooking_time_max} min). Consider simpler recipes."
            )
        
        # Ingredient recommendations
        batch_suggestions = self.suggest_batch_cooking(weekly_plan, ingredient_reuse)
        recommendations.extend(batch_suggestions)
        
        prep_suggestions = self.suggest_prep_ahead(weekly_plan)
        recommendations.extend(prep_suggestions)
        
        # Reuse recommendations
        single_use = sum(1 for count in ingredient_reuse.values() if count == 1)
        if single_use > len(ingredient_reuse) * 0.5:
            recommendations.append(
                "Consider recipes with more overlapping ingredients to reduce grocery costs"
            )
        
        # Calculate score
        score = self.calculate_optimization_score(
            cooking_stats,
            ingredient_reuse,
            cooking_time_max
        )
        
        result = ScheduleOptimizationResult(
            optimized_plan=optimized_plan,
            cooking_time_stats=cooking_stats,
            ingredient_reuse_stats=ingredient_reuse,
            optimization_score=score,
            recommendations=recommendations
        )
        
        logger.info(
            "schedule_optimized",
            score=score,
            avg_time=cooking_stats["average_per_day"],
            recommendations=len(recommendations)
        )
        
        return result


# Create global instance
schedule_optimizer = ScheduleOptimizerAgent()
