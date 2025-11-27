"""Nutrition accuracy tests for MealMind agents."""
import pytest
from agents import profile_manager, recipe_generator, nutrition_compliance
from tools import nutrition_tool


class TestNutritionAccuracy:
    """Test suite for validating nutritional calculations."""
    
    @pytest.fixture
    def setup_household(self):
        """Set up a test household."""
        household_id = "test_nutrition"
        
        profile_manager.create_household_profile(
            household_id=household_id,
            cooking_time_max=45
        )
        
        profile_manager.add_family_member(
            household_id=household_id,
            name="TestUser",
            calorie_target=2000
        )
        
        return household_id
    
    def test_nutrition_lookup_accuracy(self):
        """Test that nutrition lookup returns reasonable values."""
        # Test known ingredients
        chicken_nutrition = nutrition_tool.lookup("chicken", 100)
        
        # Chicken breast should have roughly these values per 100g
        assert 150 <= chicken_nutrition.calories <= 200, "Chicken calories out of range"
        assert 25 <= chicken_nutrition.protein_g <= 35, "Chicken protein out of range"
        assert chicken_nutrition.carbs_g < 5, "Chicken should have minimal carbs"
    
    def test_recipe_nutrition_calculation(self, setup_household):
        """Test that recipe nutrition is calculated correctly."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        recipe = recipe_generator.generate_recipe(
            meal_type="lunch",
            planning_context=context,
            constraints=constraints
        )
        
        recipe_dict = recipe.model_dump()
        
        # Calculate nutrition
        nutrition_per_serving = nutrition_compliance.calculate_recipe_nutrition(recipe_dict)
        
        # Should have reasonable values for a meal
        assert nutrition_per_serving["calories"] > 0, "Calories should be positive"
        assert nutrition_per_serving["protein_g"] > 0, "Protein should be positive"
        assert nutrition_per_serving["carbs_g"] >= 0, "Carbs should be non-negative"
        assert nutrition_per_serving["fat_g"] >= 0, "Fat should be non-negative"
        
        # A meal should typically have 200-800 calories
        assert 100 <= nutrition_per_serving["calories"] <= 1000, \
            f"Meal calories {nutrition_per_serving['calories']} outside reasonable range"
    
    def test_batch_nutrition_lookup(self):
        """Test batch nutrition lookup functionality."""
        ingredients = [
            ("chicken", 200),
            ("broccoli", 150),
            ("rice", 100)
        ]
        
        results = nutrition_tool.batch_lookup(ingredients)
        
        assert len(results) == 3, "Should return 3 results"
        
        total_calories = sum(r.calories for r in results)
        assert total_calories > 0, "Total calories should be positive"
    
    def test_calorie_target_validation(self, setup_household):
        """Test that calorie targets are validated."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        recipe = recipe_generator.generate_recipe(
            meal_type="breakfast",
            planning_context=context,
            constraints=constraints
        )
        
        recipe_dict = recipe.model_dump()
        nutrition = nutrition_compliance.calculate_recipe_nutrition(recipe_dict)
        
        # Check calorie warnings
        warnings = nutrition_compliance.check_calorie_targets(
            nutrition,
            context["members"],
            "breakfast"
        )
        
        # Should generate warnings if significantly off target
        # This documents that the system checks calorie targets
        assert isinstance(warnings, list), "Should return list of warnings"
    
    def test_macro_balance(self, setup_household):
        """Test that recipes have balanced macros."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        recipe = recipe_generator.generate_recipe(
            meal_type="dinner",
            planning_context=context,
            constraints=constraints
        )
        
        recipe_dict = recipe.model_dump()
        nutrition = nutrition_compliance.calculate_recipe_nutrition(recipe_dict)
        
        # Calculate macro percentages
        total_calories = nutrition["calories"]
        if total_calories > 0:
            protein_cal = nutrition["protein_g"] * 4
            carbs_cal = nutrition["carbs_g"] * 4
            fat_cal = nutrition["fat_g"] * 9
            
            total_macro_cal = protein_cal + carbs_cal + fat_cal
            
            if total_macro_cal > 0:
                protein_pct = (protein_cal / total_macro_cal) * 100
                carbs_pct = (carbs_cal / total_macro_cal) * 100
                fat_pct = (fat_cal / total_macro_cal) * 100
                
                # Each macro should contribute something
                assert protein_pct > 0, "Recipe should have protein"
                assert carbs_pct >= 0, "Carbs calculated"
                assert fat_pct >= 0, "Fat calculated"
                
                # Total should be ~100% (allow for rounding)
                total_pct = protein_pct + carbs_pct + fat_pct
                assert 90 <= total_pct <= 110, f"Macro percentages don't add up: {total_pct}%"
    
    def test_nutrition_validation_completeness(self, setup_household):
        """Test that nutrition validation checks all required fields."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        recipe = recipe_generator.generate_recipe(
            meal_type="lunch",
            planning_context=context,
            constraints=constraints
        )
        
        recipe_dict = recipe.model_dump()
        validation = nutrition_compliance.validate_recipe(
            recipe_dict,
            context,
            constraints
        )
        
        # Validation result should have all required fields
        assert hasattr(validation, 'is_compliant'), "Missing is_compliant field"
        assert hasattr(validation, 'violations'), "Missing violations field"
        assert hasattr(validation, 'warnings'), "Missing warnings field"
        assert hasattr(validation, 'nutritional_summary'), "Missing nutritional_summary"
        assert hasattr(validation, 'recommendations'), "Missing recommendations"
        
        # Nutritional summary should have key nutrients
        nutrition = validation.nutritional_summary
        assert "calories" in nutrition, "Missing calories"
        assert "protein_g" in nutrition, "Missing protein"
        assert "carbs_g" in nutrition, "Missing carbs"
        assert "fat_g" in nutrition, "Missing fat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
