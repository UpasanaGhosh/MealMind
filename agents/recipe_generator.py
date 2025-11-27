"""Recipe Generator Agent - Generates recipes using Gemini AI."""
from typing import Dict, List, Optional, Any
import json
from pydantic import BaseModel, Field
from config import config
from utils import get_logger

logger = get_logger(__name__)

# Import Google Generative AI (Gemini ADK)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    logger.info("google_genai_imported_successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google_genai_not_available", message="Install with: pip install google-genai")


class Recipe(BaseModel):
    """Recipe model."""
    name: str
    meal_type: str  # breakfast, lunch, dinner
    cuisine: Optional[str] = None
    cooking_time_minutes: int
    servings: int = 4
    ingredients: List[Dict[str, Any]] = Field(default_factory=list)  # [{name, amount, unit}]
    instructions: List[str] = Field(default_factory=list)
    nutritional_info: Optional[Dict[str, float]] = None
    tags: List[str] = Field(default_factory=list)
    suitable_for: List[str] = Field(default_factory=list)  # Member names


class RecipeGeneratorAgent:
    """Agent responsible for generating recipe candidates using Gemini."""
    
    def __init__(self):
        """Initialize the Recipe Generator Agent."""
        self.model_name = config.DEFAULT_MODEL
        self.temperature = config.TEMPERATURE
        
        # Initialize Gemini client if available
        if GEMINI_AVAILABLE and config.GOOGLE_API_KEY:
            try:
                self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
                self.use_gemini = True
                logger.info(
                    "recipe_generator_initialized_with_gemini",
                    model=self.model_name,
                    api_key_present=True
                )
            except Exception as e:
                self.use_gemini = False
                logger.warning(
                    "gemini_initialization_failed",
                    error=str(e),
                    fallback="using_mock_recipes"
                )
        else:
            self.use_gemini = False
            if not GEMINI_AVAILABLE:
                logger.warning("gemini_not_available", message="Using mock recipes - install google-genai to enable")
            elif not config.GOOGLE_API_KEY:
                logger.warning("no_api_key", message="Set GOOGLE_API_KEY in .env to use Gemini")
    
    def _build_recipe_prompt(
        self,
        meal_type: str,
        planning_context: Dict,
        constraints: Dict,
        additional_requirements: Optional[str] = None
    ) -> str:
        """Build a prompt for Gemini to generate a recipe.
        
        Args:
            meal_type: Type of meal (breakfast, lunch, dinner)
            planning_context: Household planning context
            constraints: Dietary constraints
            additional_requirements: Additional specific requirements
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate a {meal_type} recipe for a family with the following requirements:

**Family Members:**
"""
        for member in planning_context.get("members", []):
            prompt += f"- {member['name']}"
            if member.get('health_conditions'):
                prompt += f" (Health: {', '.join(member['health_conditions'])})"
            if member.get('dietary_restrictions'):
                prompt += f" (Diet: {', '.join(member['dietary_restrictions'])})"
            prompt += "\n"
        
        prompt += f"\n**Cooking Time Limit:** {planning_context.get('cooking_time_max', 45)} minutes maximum\n"
        
        if planning_context.get('appliances'):
            prompt += f"**Available Appliances:** {', '.join(planning_context['appliances'])}\n"
        
        prompt += "\n**Dietary Constraints:**\n"
        
        if constraints.get('allergies'):
            prompt += f"- MUST AVOID (Allergies): {', '.join(constraints['allergies'])}\n"
        
        if constraints.get('dietary_restrictions'):
            prompt += f"- Dietary Restrictions: {', '.join(constraints['dietary_restrictions'])}\n"
        
        if constraints.get('dislikes'):
            prompt += f"- Disliked Ingredients: {', '.join(constraints['dislikes'])}\n"
        
        # Health condition guidelines
        if constraints.get('health_guidelines'):
            prompt += "\n**Health Condition Guidelines:**\n"
            for condition, guidelines in constraints['health_guidelines'].items():
                prompt += f"- {condition.upper()}:\n"
                if guidelines.get('avoid'):
                    prompt += f"  - Avoid: {', '.join(guidelines['avoid'])}\n"
                if guidelines.get('prefer'):
                    prompt += f"  - Prefer: {', '.join(guidelines['prefer'])}\n"
        
        if planning_context.get('cuisine_preferences'):
            prompt += f"\n**Cuisine Preferences:** {', '.join(planning_context['cuisine_preferences'])}\n"
        
        if additional_requirements:
            prompt += f"\n**Additional Requirements:**\n{additional_requirements}\n"
        
        prompt += """
**CRITICAL INSTRUCTIONS:**
1. Ensure ALL allergies are completely avoided
2. Respect ALL dietary restrictions for each member (vegetarian = NO meat/fish, gluten-free = NO wheat/bread)
3. Use measurements in grams or ml when possible for nutrition calculation
4. Keep cooking time under the specified limit
5. Make the recipe family-friendly and practical
6. List which family members can safely eat this dish in "suitable_for"

**OUTPUT FORMAT:**
You MUST respond with ONLY valid JSON in this exact format (no other text before or after):

{
  "name": "Recipe Name",
  "meal_type": "breakfast",
  "cuisine": "cuisine type",
  "cooking_time_minutes": 30,
  "servings": 4,
  "ingredients": [
    {"name": "ingredient name", "amount": 100, "unit": "grams"},
    {"name": "another ingredient", "amount": 50, "unit": "ml"}
  ],
  "instructions": [
    "Step 1: detailed instruction",
    "Step 2: detailed instruction"
  ],
  "tags": ["tag1", "tag2"],
  "suitable_for": ["Alice", "Bob"]
}

CRITICAL: Return ONLY the JSON object, nothing else. Do not include explanations, markdown formatting, or any text outside the JSON.
"""
        
        return prompt
    
    def generate_recipe(
        self,
        meal_type: str,
        planning_context: Dict,
        constraints: Dict,
        additional_requirements: Optional[str] = None,
        retry_count: int = 0
    ) -> Recipe:
        """Generate a single recipe using Gemini.
        
        Args:
            meal_type: Type of meal (breakfast, lunch, dinner)
            planning_context: Household planning context
            constraints: Dietary constraints
            additional_requirements: Additional requirements
            retry_count: Number of retries (for tracking)
            
        Returns:
            Generated recipe
        """
        logger.info(
            "generating_recipe",
            meal_type=meal_type,
            household_id=planning_context.get('household_id'),
            retry=retry_count
        )
        
        prompt = self._build_recipe_prompt(
            meal_type,
            planning_context,
            constraints,
            additional_requirements
        )
        
        # Try to use Gemini API if available
        if self.use_gemini:
            try:
                logger.info("calling_gemini_api", meal_type=meal_type)
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=2048,
                    )
                )
                
                # Extract and parse JSON from response
                response_text = response.text.strip()
                
                # Handle markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                recipe_data = json.loads(response_text)
                
                logger.info(
                    "gemini_recipe_generated_successfully",
                    recipe_name=recipe_data.get("name"),
                    cooking_time=recipe_data.get("cooking_time_minutes")
                )
                
            except json.JSONDecodeError as e:
                logger.error(
                    "gemini_json_parse_error",
                    error=str(e),
                    response_preview=response_text[:200] if 'response_text' in locals() else "N/A",
                    fallback="using_mock_recipe"
                )
                # Fallback to mock recipe
                recipe_data = self._generate_mock_recipe(meal_type, planning_context, constraints)
            
            except Exception as e:
                logger.error(
                    "gemini_api_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    fallback="using_mock_recipe"
                )
                # Fallback to mock recipe
                recipe_data = self._generate_mock_recipe(meal_type, planning_context, constraints)
        else:
            # Use mock recipe generation (no Gemini available)
            logger.info("using_mock_recipe", reason="gemini_not_available")
            recipe_data = self._generate_mock_recipe(meal_type, planning_context, constraints)
        
        recipe = Recipe(**recipe_data)
        
        logger.info(
            "recipe_generated",
            name=recipe.name,
            meal_type=meal_type,
            cooking_time=recipe.cooking_time_minutes
        )
        
        return recipe
    
    def _generate_mock_recipe(
        self,
        meal_type: str,
        planning_context: Dict,
        constraints: Dict
    ) -> Dict:
        """Generate a mock recipe for testing.
        
        This will be replaced with actual Gemini generation.
        
        Args:
            meal_type: Type of meal
            planning_context: Planning context
            constraints: Constraints
            
        Returns:
            Mock recipe data
        """
        # Determine dietary tags and restrictions
        tags = []
        restrictions = [r.lower() for r in constraints.get('dietary_restrictions', [])]
        is_vegetarian = "vegetarian" in restrictions or "vegan" in restrictions
        is_gluten_free = "gluten-free" in restrictions
        is_vegan = "vegan" in restrictions
        
        if is_vegan:
            tags.append("vegan")
        if is_gluten_free:
            tags.append("gluten-free")
        
        # Mock recipes based on meal type and constraints
        if meal_type == "breakfast":
            if is_gluten_free and not is_vegetarian:
                recipe = {
                    "name": "Scrambled Eggs with Roasted Vegetables",
                    "meal_type": "breakfast",
                    "cuisine": "American",
                    "cooking_time_minutes": 25,
                    "servings": 4,
                    "ingredients": [
                        {"name": "eggs", "amount": 8, "unit": "pieces"},
                        {"name": "bell pepper", "amount": 150, "unit": "grams"},
                        {"name": "onion", "amount": 100, "unit": "grams"},
                        {"name": "tomato", "amount": 150, "unit": "grams"},
                        {"name": "olive oil", "amount": 20, "unit": "ml"},
                        {"name": "potato", "amount": 300, "unit": "grams"}
                    ],
                    "instructions": [
                        "Dice potatoes and roast at 400°F for 15 minutes",
                        "Chop vegetables into small pieces",
                        "Heat olive oil in a pan over medium heat",
                        "Sauté onions, peppers, and tomatoes for 5 minutes",
                        "Beat eggs in a bowl and pour into pan",
                        "Scramble until cooked through",
                        "Serve with roasted potatoes"
                    ],
                    "tags": tags + ["high-protein", "gluten-free"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', []) 
                                    if 'vegetarian' not in [r.lower() for r in m.get('dietary_restrictions', [])]]
                }
            elif is_vegetarian:
                recipe = {
                    "name": "Oatmeal with Fruits and Nuts",
                    "meal_type": "breakfast",
                    "cuisine": "American",
                    "cooking_time_minutes": 15,
                    "servings": 4,
                    "ingredients": [
                        {"name": "oats", "amount": 300, "unit": "grams"},
                        {"name": "banana", "amount": 400, "unit": "grams"},
                        {"name": "blueberries", "amount": 200, "unit": "grams"},
                        {"name": "walnuts", "amount": 100, "unit": "grams"},
                        {"name": "honey", "amount": 60, "unit": "ml"},
                        {"name": "cinnamon", "amount": 5, "unit": "grams"}
                    ],
                    "instructions": [
                        "Cook oats in water according to package directions",
                        "Slice bananas",
                        "Divide oatmeal into 4 bowls",
                        "Top with bananas, blueberries, and walnuts",
                        "Drizzle with honey and sprinkle cinnamon",
                        "Serve warm"
                    ],
                    "tags": tags + ["vegetarian", "high-fiber"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])]
                }
            else:
                recipe = {
                    "name": "Vegetable Omelette with Potatoes",
                    "meal_type": "breakfast",
                    "cuisine": "American",
                    "cooking_time_minutes": 20,
                    "servings": 4,
                    "ingredients": [
                        {"name": "eggs", "amount": 8, "unit": "pieces"},
                        {"name": "bell pepper", "amount": 150, "unit": "grams"},
                        {"name": "onion", "amount": 100, "unit": "grams"},
                        {"name": "tomato", "amount": 100, "unit": "grams"},
                        {"name": "potato", "amount": 300, "unit": "grams"},
                        {"name": "olive oil", "amount": 20, "unit": "ml"}
                    ],
                    "instructions": [
                        "Chop vegetables and potato into small pieces",
                        "Heat olive oil in a pan over medium heat",
                        "Sauté potatoes for 10 minutes until golden",
                        "Add onions and bell peppers, cook 3 minutes",
                        "Beat eggs in a bowl and pour over vegetables",
                        "Cook until eggs are set, about 5 minutes",
                        "Serve hot"
                    ],
                    "tags": tags + ["high-protein", "vegetarian"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])]
                }
        elif meal_type == "lunch":
            if is_vegetarian:
                recipe = {
                    "name": "Mediterranean Quinoa Bowl",
                    "meal_type": "lunch",
                    "cuisine": "Mediterranean",
                    "cooking_time_minutes": 30,
                    "servings": 4,
                    "ingredients": [
                        {"name": "quinoa", "amount": 300, "unit": "grams"},
                        {"name": "chickpeas", "amount": 400, "unit": "grams"},
                        {"name": "cherry tomatoes", "amount": 200, "unit": "grams"},
                        {"name": "cucumber", "amount": 150, "unit": "grams"},
                        {"name": "red onion", "amount": 100, "unit": "grams"},
                        {"name": "olive oil", "amount": 40, "unit": "ml"},
                        {"name": "lemon juice", "amount": 30, "unit": "ml"},
                        {"name": "feta cheese", "amount": 100, "unit": "grams"}
                    ],
                    "instructions": [
                        "Cook quinoa according to package instructions",
                        "Drain and rinse chickpeas",
                        "Chop all vegetables",
                        "Mix quinoa, chickpeas, and vegetables in large bowl",
                        "Whisk together olive oil and lemon juice",
                        "Pour dressing over salad and toss",
                        "Top with crumbled feta cheese"
                    ],
                    "tags": tags + ["vegetarian", "high-protein", "mediterranean"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])]
                }
            else:
                recipe = {
                    "name": "Grilled Chicken Salad Bowl",
                    "meal_type": "lunch",
                    "cuisine": "Mediterranean",
                    "cooking_time_minutes": 30,
                    "servings": 4,
                    "ingredients": [
                        {"name": "chicken breast", "amount": 600, "unit": "grams"},
                        {"name": "mixed greens", "amount": 200, "unit": "grams"},
                        {"name": "cherry tomatoes", "amount": 200, "unit": "grams"},
                        {"name": "cucumber", "amount": 150, "unit": "grams"},
                        {"name": "quinoa", "amount": 200, "unit": "grams"},
                        {"name": "olive oil", "amount": 30, "unit": "ml"},
                        {"name": "lemon juice", "amount": 30, "unit": "ml"}
                    ],
                    "instructions": [
                        "Cook quinoa according to package instructions",
                        "Season chicken with salt, pepper, and herbs",
                        "Grill chicken for 6-7 minutes per side until cooked through",
                        "Chop vegetables while chicken cooks",
                        "Slice cooked chicken into strips",
                        "Assemble bowls with quinoa, greens, vegetables, and chicken",
                        "Drizzle with olive oil and lemon juice"
                    ],
                    "tags": tags + ["high-protein", "low-carb"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])
                                    if 'vegetarian' not in [r.lower() for r in m.get('dietary_restrictions', [])]]
                }
        else:  # dinner
            if is_vegetarian:
                recipe = {
                    "name": "Vegetable Stir-Fry with Tofu",
                    "meal_type": "dinner",
                    "cuisine": "Asian",
                    "cooking_time_minutes": 35,
                    "servings": 4,
                    "ingredients": [
                        {"name": "firm tofu", "amount": 400, "unit": "grams"},
                        {"name": "broccoli", "amount": 300, "unit": "grams"},
                        {"name": "bell pepper", "amount": 200, "unit": "grams"},
                        {"name": "carrot", "amount": 150, "unit": "grams"},
                        {"name": "snap peas", "amount": 200, "unit": "grams"},
                        {"name": "rice", "amount": 300, "unit": "grams"},
                        {"name": "soy sauce", "amount": 40, "unit": "ml"},
                        {"name": "sesame oil", "amount": 20, "unit": "ml"},
                        {"name": "garlic", "amount": 15, "unit": "grams"},
                        {"name": "ginger", "amount": 10, "unit": "grams"}
                    ],
                    "instructions": [
                        "Cook rice according to package instructions",
                        "Press and cube tofu, then pan-fry until golden",
                        "Chop all vegetables into bite-sized pieces",
                        "Heat sesame oil in wok or large pan",
                        "Stir-fry garlic and ginger for 30 seconds",
                        "Add vegetables and stir-fry for 5-7 minutes",
                        "Add tofu and soy sauce, toss to combine",
                        "Serve over rice"
                    ],
                    "tags": tags + ["vegetarian", "high-protein", "asian"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])]
                }
            else:
                recipe = {
                    "name": "Baked Salmon with Roasted Vegetables",
                    "meal_type": "dinner",
                    "cuisine": "American",
                    "cooking_time_minutes": 40,
                    "servings": 4,
                    "ingredients": [
                        {"name": "salmon", "amount": 600, "unit": "grams"},
                        {"name": "broccoli", "amount": 300, "unit": "grams"},
                        {"name": "sweet potato", "amount": 400, "unit": "grams"},
                        {"name": "carrot", "amount": 200, "unit": "grams"},
                        {"name": "olive oil", "amount": 40, "unit": "ml"},
                        {"name": "garlic", "amount": 20, "unit": "grams"},
                        {"name": "lemon", "amount": 2, "unit": "pieces"}
                    ],
                    "instructions": [
                        "Preheat oven to 400°F (200°C)",
                        "Cut vegetables into bite-sized pieces",
                        "Toss vegetables with olive oil, minced garlic, salt, and pepper",
                        "Spread vegetables on baking sheet and roast for 20 minutes",
                        "Season salmon with salt, pepper, and lemon juice",
                        "Place salmon on same baking sheet with vegetables",
                        "Roast for additional 15-20 minutes until salmon is cooked through",
                        "Serve hot with lemon wedges"
                    ],
                    "tags": tags + ["high-protein", "omega-3", "healthy-fats"],
                    "suitable_for": [m['name'] for m in planning_context.get('members', [])
                                    if 'vegetarian' not in [r.lower() for r in m.get('dietary_restrictions', [])]]
                }
        
        return recipe
    
    def generate_weekly_meals(
        self,
        planning_context: Dict,
        constraints: Dict,
        days: int = 7
    ) -> List[Dict]:
        """Generate meals for multiple days.
        
        Args:
            planning_context: Household planning context
            constraints: Dietary constraints
            days: Number of days to plan for
            
        Returns:
            List of daily meal plans
        """
        logger.info(
            "generating_weekly_meals",
            household_id=planning_context.get('household_id'),
            days=days
        )
        
        weekly_plan = []
        
        for day_num in range(1, days + 1):
            day_meals = {
                "day": day_num,
                "meals": []
            }
            
            # Generate breakfast, lunch, dinner
            for meal_type in ["breakfast", "lunch", "dinner"]:
                recipe = self.generate_recipe(
                    meal_type=meal_type,
                    planning_context=planning_context,
                    constraints=constraints
                )
                day_meals["meals"].append(recipe.model_dump())
            
            weekly_plan.append(day_meals)
        
        logger.info("weekly_meals_generated", days=days)
        return weekly_plan
    
    def regenerate_recipe(
        self,
        original_recipe: Recipe,
        feedback: str,
        planning_context: Dict,
        constraints: Dict
    ) -> Recipe:
        """Regenerate a recipe based on feedback.
        
        This is used when a recipe fails nutrition compliance or other checks.
        
        Args:
            original_recipe: The original recipe that needs modification
            feedback: Specific feedback on what needs to change
            planning_context: Household planning context
            constraints: Dietary constraints
            
        Returns:
            Regenerated recipe
        """
        logger.info(
            "regenerating_recipe",
            original_name=original_recipe.name,
            feedback=feedback
        )
        
        additional_requirements = f"""
Previous recipe "{original_recipe.name}" had issues:
{feedback}

Please generate a NEW recipe that addresses these issues.
"""
        
        return self.generate_recipe(
            meal_type=original_recipe.meal_type,
            planning_context=planning_context,
            constraints=constraints,
            additional_requirements=additional_requirements,
            retry_count=1
        )


# Create global instance
recipe_generator = RecipeGeneratorAgent()
