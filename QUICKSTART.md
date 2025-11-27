# 🚀 MealMind Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Navigate to project
cd /Users/anasaura/workplace/mealMind

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

## Run the Demo

```bash
# Run complete multi-agent demo
python complete_demo.py
```

## What the Demo Shows

✅ **Profile Management** - Creates a household with 4 family members:
- Alice: PCOS, low-GI diet
- Bob: Peanut allergy, gluten-free
- Charlie: Vegetarian, dislikes spinach
- Diana: Normal diet

✅ **Recipe Generation** - Generates 9 meals (3 days × 3 meals/day)
- Respects all dietary restrictions
- Validates nutrition compliance
- Automatic retry loop for failed recipes

✅ **Nutrition Validation** - Each recipe validated for:
- Allergen detection (peanuts)
- Dietary restrictions (vegetarian, gluten-free)
- Health conditions (PCOS guidelines)
- Calorie targets per member

✅ **Schedule Optimization** - Analyzes:
- Cooking time per day
- Ingredient reuse efficiency
- Batch cooking opportunities
- Prep-ahead suggestions

✅ **Grocery List** - Organized shopping list with:
- 24 unique ingredients
- Cost estimation ($85.88)
- Categorized by aisle
- Shopping tips and bulk-buy suggestions

## Output

After running, check:
- **meal_plan_output.json** - Complete meal plan data
- **memory/profiles.json** - Stored family profiles
- **memory/long_term_memory.json** - Historical data

## Gemini AI Integration (Optional)

MealMind works with **both** mock recipes and real Gemini AI:

### Current: Mock Mode (No API Key Needed)
- Uses intelligent mock recipes
- Works immediately
- Perfect for testing

### Enhanced: Gemini Mode (5 minutes to enable)

**Step 1:** Get free API key from [Google AI Studio](https://aistudio.google.com/apikey)

**Step 2:** Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_key_here
```

**Step 3:** Run demo:
```bash
python complete_demo.py
# System automatically uses Gemini when API key is present!
```

**Benefits:**
- 🎨 Unique recipes each time
- 🧠 Real AI creativity
- ✨ True LLM-powered generation
- 💰 Cost: < $0.01 per run (essentially free!)

## Example Output

```
📅 DAY 1
  BREAKFAST: Oatmeal with Fruits and Nuts (15 min)
  LUNCH: Mediterranean Quinoa Bowl (30 min)
  DINNER: Vegetable Stir-Fry with Tofu (35 min)

📊 Optimization Score: 91.7/100
💰 Total Cost: $85.88 (within $150 budget)
♻️  Ingredient Reuse: 100%
```

## Troubleshooting

**Import Errors:**
- Ensure venv is activated: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**Gemini Status:**
```bash
# Check if Gemini is enabled
python -c "from agents.recipe_generator import recipe_generator; print('Using Gemini:', recipe_generator.use_gemini)"
```

**View Logs:**
```bash
cat logs/mealmind.log | grep gemini
```

## Next Steps

1. ✅ Run demo: `python complete_demo.py`
2. 💡 Add your API key for live Gemini generation
3. 📊 Review `meal_plan_output.json` for full details
4. 🎓 Use for capstone presentation!
