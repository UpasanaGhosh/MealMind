"""Complete MealMind Demo - Shows full multi-agent orchestration."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import orchestrator
from agents import profile_manager
import json


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def setup_demo_household():
    """Set up a demo household with diverse needs."""
    print_section("SETTING UP DEMO HOUSEHOLD")
    
    # Create household
    print("Creating household profile...")
    household = profile_manager.create_household_profile(
        household_id="demo_family_complete",
        cooking_time_max=45,
        appliances=["oven", "stove", "microwave", "blender"],
        budget_weekly=150.0,
        cuisine_preferences=["Mediterranean", "Asian", "Italian"]
    )
    print(f"✓ Household '{household['household_id']}' created")
    
    # Add family members with diverse needs
    print("\nAdding family members...")
    
    members = [
        {
            "name": "Alice",
            "age": 35,
            "health_conditions": ["PCOS"],
            "dietary_restrictions": ["low-GI"],
            "preferences": ["spicy", "asian cuisine"],
            "calorie_target": 1800
        },
        {
            "name": "Bob",
            "age": 37,
            "allergies": ["peanuts"],
            "dietary_restrictions": ["gluten-free"],
            "dislikes": ["mushrooms"],
            "calorie_target": 2200
        },
        {
            "name": "Charlie",
            "age": 12,
            "dietary_restrictions": ["vegetarian"],
            "preferences": ["pasta", "pizza"],
            "dislikes": ["spinach"],
            "calorie_target": 1600
        },
        {
            "name": "Diana",
            "age": 10,
            "preferences": ["chicken", "rice"],
            "calorie_target": 1400
        }
    ]
    
    for member_data in members:
        profile_manager.add_family_member(
            household_id="demo_family_complete",
            **member_data
        )
        print(f"✓ Added {member_data['name']}")
    
    print("\n✓ Household setup complete with 4 family members")


def generate_meal_plan():
    """Generate a complete meal plan using the orchestrator."""
    print_section("GENERATING COMPLETE MEAL PLAN")
    
    print("Starting multi-agent orchestration...")
    print("This will:")
    print("  1. Load household profiles and constraints")
    print("  2. Generate recipes for each meal")
    print("  3. Validate nutrition compliance (with retry loop)")
    print("  4. Optimize the weekly schedule")
    print("  5. Create organized grocery list")
    print()
    
    # Generate 3-day plan for demo (faster)
    print("Generating 3-day meal plan...\n")
    
    meal_plan = orchestrator.quick_plan(
        household_id="demo_family_complete",
        days=3
    )
    
    print("\n✓ Meal plan generation complete!")
    
    return meal_plan


def display_meal_plan(meal_plan):
    """Display the complete meal plan."""
    print_section("COMPLETE MEAL PLAN")
    
    # Use orchestrator's summary method
    summary = orchestrator.generate_meal_plan_summary(meal_plan)
    print(summary)


def display_grocery_list(meal_plan):
    """Display the grocery list."""
    print_section("GROCERY LIST")
    
    print(meal_plan["shopping_checklist"])


def display_statistics(meal_plan):
    """Display statistics and insights."""
    print_section("PLAN STATISTICS & INSIGHTS")
    
    # Count meals
    total_meals = sum(len(day["meals"]) for day in meal_plan["weekly_plan"])
    print(f"📊 Total Meals Generated: {total_meals}")
    
    # Count validated recipes
    validated = sum(
        1 for day in meal_plan["weekly_plan"]
        for meal in day["meals"]
        if meal.get("nutrition_validated")
    )
    print(f"✓ Nutrition Validated: {validated}/{total_meals}")
    
    # Optimization score
    opt_score = meal_plan["optimization"]["optimization_score"]
    print(f"📈 Optimization Score: {opt_score:.1f}/100")
    
    # Cost
    total_cost = meal_plan["grocery_list"]["total_estimated_cost"]
    budget = 150.0
    print(f"💰 Total Cost: ${total_cost:.2f}")
    print(f"💵 Budget: ${budget:.2f}")
    print(f"{'✓ Within budget!' if total_cost <= budget else '⚠️ Over budget'}")
    
    # Ingredient reuse
    ingredient_reuse = meal_plan["optimization"]["ingredient_reuse_stats"]
    reused = sum(1 for count in ingredient_reuse.values() if count >= 2)
    total_unique = len(ingredient_reuse)
    reuse_pct = (reused / total_unique * 100) if total_unique > 0 else 0
    print(f"\n♻️  Ingredient Reuse: {reuse_pct:.0f}% ({reused}/{total_unique} ingredients)")
    
    # Cooking time
    cooking_stats = meal_plan["optimization"]["cooking_time_stats"]
    avg_time = cooking_stats["average_per_day"]
    max_limit = 45
    print(f"\n⏱️  Average Cooking Time: {avg_time:.0f} min/day")
    print(f"{'✓ Within limit!' if avg_time <= max_limit else '⚠️ Exceeds limit'}")
    
    # Top reused ingredients
    top_ingredients = sorted(
        ingredient_reuse.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    print(f"\n🔝 Most Used Ingredients:")
    for ing, count in top_ingredients:
        print(f"   • {ing.title()}: {count}x")


def save_plan_to_file(meal_plan):
    """Save the meal plan to a JSON file."""
    output_file = Path(__file__).parent / "meal_plan_output.json"
    
    with open(output_file, 'w') as f:
        json.dump(meal_plan, f, indent=2)
    
    print(f"\n💾 Full meal plan saved to: {output_file}")


def main():
    """Run the complete demo."""
    print("\n" + "🌱" * 35)
    print("   MEALMIND COMPLETE DEMO")
    print("   Multi-Agent Family Meal Planning System")
    print("   WITH FULL ORCHESTRATION")
    print("🌱" * 35)
    
    try:
        # Step 1: Setup
        setup_demo_household()
        
        # Step 2: Generate plan
        meal_plan = generate_meal_plan()
        
        # Step 3: Display results
        display_meal_plan(meal_plan)
        display_grocery_list(meal_plan)
        display_statistics(meal_plan)
        
        # Step 4: Save to file
        save_plan_to_file(meal_plan)
        
        # Final summary
        print("\n" + "=" * 70)
        print("  DEMO COMPLETE ✓")
        print("=" * 70)
        print("\n🎉 Successfully demonstrated:")
        print("   ✓ Profile Management (4 family members with diverse needs)")
        print("   ✓ Recipe Generation (9 meals across 3 days)")
        print("   ✓ Nutrition Validation (with automatic retry loop)")
        print("   ✓ Schedule Optimization (time & ingredient analysis)")
        print("   ✓ Grocery List Generation (organized by category)")
        print("   ✓ Multi-Agent Orchestration (all 5 agents working together)")
        print("\n💡 Next Steps:")
        print("   1. Review meal_plan_output.json for full details")
        print("   2. Add your Google API key to integrate with Gemini")
        print("   3. Run with 7 days for a full weekly plan")
        print("   4. Try the Streamlit UI (coming soon)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
