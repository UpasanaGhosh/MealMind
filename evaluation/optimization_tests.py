"""Optimization tests for MealMind schedule optimizer agent."""
import pytest
from agents import profile_manager, recipe_generator, schedule_optimizer, grocery_agent
from tools import cost_estimator


class TestOptimization:
    """Test suite for schedule and cost optimization."""
    
    @pytest.fixture
    def setup_household(self):
        """Set up a test household."""
        household_id = "test_optimization"
        
        profile_manager.create_household_profile(
            household_id=household_id,
            cooking_time_max=45,
            budget_weekly=150.0
        )
        
        profile_manager.add_family_member(
            household_id=household_id,
            name="TestUser"
        )
        
        return household_id
    
    @pytest.fixture
    def generate_test_plan(self, setup_household):
        """Generate a test meal plan."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        # Generate 3-day plan
        weekly_plan = recipe_generator.generate_weekly_meals(
            planning_context=context,
            constraints=constraints,
            days=3
        )
        
        return weekly_plan, context
    
    def test_cooking_time_analysis(self, generate_test_plan):
        """Test cooking time analysis functionality."""
        weekly_plan, context = generate_test_plan
        
        stats = schedule_optimizer.analyze_cooking_times(weekly_plan)
        
        # Should have all required stats
        assert "total_minutes" in stats, "Missing total_minutes"
        assert "average_per_day" in stats, "Missing average_per_day"
        assert "max_day" in stats, "Missing max_day"
        assert "min_day" in stats, "Missing min_day"
        assert "daily_times" in stats, "Missing daily_times"
        
        # Values should be reasonable
        assert stats["total_minutes"] >= 0, "Total time should be non-negative"
        assert stats["average_per_day"] >= 0, "Average should be non-negative"
        assert len(stats["daily_times"]) == 3, "Should have 3 days of data"
    
    def test_ingredient_reuse_analysis(self, generate_test_plan):
        """Test ingredient reuse analysis."""
        weekly_plan, context = generate_test_plan
        
        ingredient_reuse = schedule_optimizer.analyze_ingredient_reuse(weekly_plan)
        
        # Should return a dictionary
        assert isinstance(ingredient_reuse, dict), "Should return dictionary"
        
        # Should have ingredients
        assert len(ingredient_reuse) > 0, "Should have some ingredients"
        
        # All counts should be positive
        for ingredient, count in ingredient_reuse.items():
            assert count > 0, f"{ingredient} has non-positive count"
    
    def test_optimization_score_calculation(self, generate_test_plan):
        """Test optimization score calculation."""
        weekly_plan, context = generate_test_plan
        
        stats = schedule_optimizer.analyze_cooking_times(weekly_plan)
        ingredient_reuse = schedule_optimizer.analyze_ingredient_reuse(weekly_plan)
        
        score = schedule_optimizer.calculate_optimization_score(
            stats,
            ingredient_reuse,
            cooking_time_max=45
        )
        
        # Score should be between 0 and 100
        assert 0 <= score <= 100, f"Score {score} outside valid range"
    
    def test_schedule_optimization_result(self, generate_test_plan):
        """Test complete schedule optimization."""
        weekly_plan, context = generate_test_plan
        
        result = schedule_optimizer.optimize_schedule(
            weekly_plan,
            cooking_time_max=45
        )
        
        # Should have all required fields
        assert result.optimized_plan is not None, "Missing optimized_plan"
        assert result.cooking_time_stats is not None, "Missing cooking_time_stats"
        assert result.ingredient_reuse_stats is not None, "Missing ingredient_reuse_stats"
        assert result.optimization_score is not None, "Missing optimization_score"
        assert result.recommendations is not None, "Missing recommendations"
        
        # Optimized plan should have same number of days
        assert len(result.optimized_plan) == len(weekly_plan), "Day count mismatch"
    
    def test_batch_cooking_suggestions(self, generate_test_plan):
        """Test batch cooking suggestion generation."""
        weekly_plan, context = generate_test_plan
        
        ingredient_reuse = schedule_optimizer.analyze_ingredient_reuse(weekly_plan)
        suggestions = schedule_optimizer.suggest_batch_cooking(weekly_plan, ingredient_reuse)
        
        # Should return a list
        assert isinstance(suggestions, list), "Should return list"
        
        # If ingredients are reused 3+ times, should have suggestions
        frequent_ingredients = [ing for ing, count in ingredient_reuse.items() if count >= 3]
        if frequent_ingredients:
            assert len(suggestions) > 0, "Should suggest batch cooking for frequent ingredients"
    
    def test_cost_estimation_accuracy(self):
        """Test cost estimation calculations."""
        # Test single ingredient
        cost_info = cost_estimator.estimate_ingredient_cost("chicken", 500)
        
        assert cost_info.estimated_cost > 0, "Cost should be positive"
        assert cost_info.price_per_kg > 0, "Price per kg should be positive"
        assert cost_info.category is not None, "Should have category"
    
    def test_recipe_cost_estimation(self, generate_test_plan):
        """Test recipe cost estimation."""
        weekly_plan, context = generate_test_plan
        
        # Get first recipe
        recipe = weekly_plan[0]["meals"][0]
        
        # Estimate cost
        ingredients = [
            (ing["name"], ing["amount"]) 
            for ing in recipe["ingredients"]
            if ing.get("unit") == "grams" or ing.get("unit") == "ml"
        ]
        
        if ingredients:
            recipe_cost = cost_estimator.estimate_recipe_cost(ingredients)
            
            assert "total_cost" in recipe_cost, "Missing total_cost"
            assert "category_breakdown" in recipe_cost, "Missing category_breakdown"
            assert recipe_cost["total_cost"] >= 0, "Cost should be non-negative"
    
    def test_grocery_list_generation(self, generate_test_plan):
        """Test grocery list generation and aggregation."""
        weekly_plan, context = generate_test_plan
        
        grocery_list = grocery_agent.create_grocery_list(
            weekly_plan,
            budget=150.0
        )
        
        # Should have all required fields
        assert grocery_list.total_items > 0, "Should have items"
        assert grocery_list.total_estimated_cost >= 0, "Cost should be non-negative"
        assert len(grocery_list.items_by_category) > 0, "Should have categories"
        assert len(grocery_list.shopping_tips) > 0, "Should have tips"
    
    def test_ingredient_aggregation(self, generate_test_plan):
        """Test that ingredients are properly aggregated."""
        weekly_plan, context = generate_test_plan
        
        aggregated = grocery_agent.aggregate_ingredients(weekly_plan)
        
        # Should aggregate ingredients from all meals
        assert len(aggregated) > 0, "Should have aggregated ingredients"
        
        # Check aggregation structure
        for ing_name, data in aggregated.items():
            assert "total_amount" in data, f"{ing_name} missing total_amount"
            assert "unit" in data, f"{ing_name} missing unit"
            assert "meals" in data, f"{ing_name} missing meals list"
            assert data["total_amount"] > 0, f"{ing_name} has non-positive amount"
    
    def test_optimization_within_budget(self, generate_test_plan):
        """Test that meal plans can stay within budget."""
        weekly_plan, context = generate_test_plan
        
        grocery_list = grocery_agent.create_grocery_list(
            weekly_plan,
            budget=150.0
        )
        
        # Cost should be calculated
        assert grocery_list.total_estimated_cost > 0, "Should have estimated cost"
        
        # For a 3-day plan, should be reasonable
        assert grocery_list.total_estimated_cost < 200, "Cost seems too high for 3 days"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
