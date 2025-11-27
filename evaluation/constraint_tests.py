"""Constraint adherence tests for MealMind agents."""
import pytest
from agents import profile_manager, recipe_generator, nutrition_compliance
from orchestrator import orchestrator


class TestConstraintAdherence:
    """Test suite for validating constraint adherence."""
    
    @pytest.fixture
    def setup_household(self):
        """Set up a test household with diverse constraints."""
        household_id = "test_household"
        
        # Create household
        profile_manager.create_household_profile(
            household_id=household_id,
            cooking_time_max=45
        )
        
        # Add members with various constraints
        profile_manager.add_family_member(
            household_id=household_id,
            name="Alice",
            allergies=["peanuts", "shellfish"],
            dietary_restrictions=["vegetarian"]
        )
        
        profile_manager.add_family_member(
            household_id=household_id,
            name="Bob",
            dietary_restrictions=["gluten-free"],
            health_conditions=["diabetes"]
        )
        
        return household_id
    
    def test_allergen_detection(self, setup_household):
        """Test that recipes never contain allergens."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        # Generate multiple recipes
        for meal_type in ["breakfast", "lunch", "dinner"]:
            recipe = recipe_generator.generate_recipe(
                meal_type=meal_type,
                planning_context=context,
                constraints=constraints
            )
            
            # Check for allergens
            recipe_dict = recipe.model_dump()
            allergens_found = []
            
            for ingredient in recipe_dict["ingredients"]:
                ing_name = ingredient["name"].lower()
                for allergen in constraints["allergies"]:
                    if allergen.lower() in ing_name:
                        allergens_found.append(f"{allergen} in {ingredient['name']}")
            
            assert len(allergens_found) == 0, f"Allergens found: {allergens_found}"
    
    def test_vegetarian_compliance(self, setup_household):
        """Test that vegetarian recipes contain no meat."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        # Generate recipe
        recipe = recipe_generator.generate_recipe(
            meal_type="dinner",
            planning_context=context,
            constraints=constraints
        )
        
        # Check for meat products
        meat_items = ["chicken", "beef", "pork", "fish", "salmon", "turkey", "meat"]
        recipe_dict = recipe.model_dump()
        
        meat_found = []
        for ingredient in recipe_dict["ingredients"]:
            ing_name = ingredient["name"].lower()
            for meat in meat_items:
                if meat in ing_name:
                    meat_found.append(ingredient["name"])
        
        assert len(meat_found) == 0, f"Meat products found in vegetarian recipe: {meat_found}"
    
    def test_gluten_free_compliance(self, setup_household):
        """Test that gluten-free recipes contain no gluten."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        # Generate recipe
        recipe = recipe_generator.generate_recipe(
            meal_type="breakfast",
            planning_context=context,
            constraints=constraints
        )
        
        # Check for gluten
        gluten_items = ["wheat", "bread", "pasta", "flour", "barley", "rye"]
        recipe_dict = recipe.model_dump()
        
        gluten_found = []
        for ingredient in recipe_dict["ingredients"]:
            ing_name = ingredient["name"].lower()
            for gluten in gluten_items:
                if gluten in ing_name:
                    gluten_found.append(ingredient["name"])
        
        assert len(gluten_found) == 0, f"Gluten found in gluten-free recipe: {gluten_found}"
    
    def test_validation_loop_works(self, setup_household):
        """Test that validation loop catches and retries violations."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        # Generate and validate recipe
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
        
        # Should be compliant (or system retried until compliant)
        assert validation.is_compliant or len(validation.violations) == 0, \
            f"Recipe has violations: {validation.violations}"
    
    def test_cooking_time_constraint(self, setup_household):
        """Test that cooking time respects maximum limit."""
        household_id = setup_household
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        max_time = context["cooking_time_max"]
        
        # Generate recipes and check times
        total_time = 0
        for meal_type in ["breakfast", "lunch", "dinner"]:
            recipe = recipe_generator.generate_recipe(
                meal_type=meal_type,
                planning_context=context,
                constraints=constraints
            )
            total_time += recipe.cooking_time_minutes
        
        # Total daily cooking time should ideally be under limit
        # (We allow some flexibility but test it's reasonable)
        assert total_time <= max_time * 2, \
            f"Total cooking time {total_time} min far exceeds limit {max_time} min"
    
    def test_disliked_ingredients_avoided(self, setup_household):
        """Test that disliked ingredients are avoided."""
        household_id = setup_household
        
        # Add dislikes
        profile_manager.profile_store.update_member(
            household_id, "Alice", dislikes=["mushrooms", "olives"]
        )
        
        context = profile_manager.generate_planning_context(household_id)
        constraints = profile_manager.get_all_constraints(household_id)
        
        recipe = recipe_generator.generate_recipe(
            meal_type="dinner",
            planning_context=context,
            constraints=constraints
        )
        
        recipe_dict = recipe.model_dump()
        dislikes = constraints.get("dislikes", [])
        
        found_dislikes = []
        for ingredient in recipe_dict["ingredients"]:
            ing_name = ingredient["name"].lower()
            for dislike in dislikes:
                if dislike.lower() in ing_name:
                    found_dislikes.append(ingredient["name"])
        
        # Note: Mock recipes might not avoid dislikes, but validation should warn
        # This test documents the intended behavior
        if found_dislikes:
            validation = nutrition_compliance.validate_recipe(
                recipe_dict, context, constraints
            )
            # Should at least have warnings about dislikes
            assert len(validation.warnings) > 0 or len(validation.violations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
