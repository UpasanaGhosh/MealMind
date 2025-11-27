# 🌱 MealMind: A Multi-Agent Family Meal Planning Concierge
An Agentic Meal Planner Using Google ADK + Gemini | Kaggle X Google Intensive Capstone Project

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🧭 Overview

MealMind is an intelligent multi-agent meal planning assistant designed to create weekly meal plans for individuals and families, especially when multiple people have overlapping or conflicting dietary needs.

Unlike typical meal apps that serve a single user, MealMind uses LLM-driven reasoning, multi-agent collaboration, and structured tools to:

- ✅ Generate a 7-day meal plan for a whole family
- ✅ Respect health conditions (e.g., diabetes, PCOS, high BP)
- ✅ Consider allergies, dislikes, and preferences
- ✅ Optimize for cooking time and shared ingredients
- ✅ Produce a grocery list
- ✅ Track long-term preferences and constraints

This project demonstrates key concepts from the Google ADK + Gemini Kaggle Intensive, including **multi-agent systems**, **tool integration**, **memory**, **observability**, **agent loops**, and **evaluation**.

---

## ⭐ Key Features

### 🧠 1. Multi-Agent System

MealMind is built using multiple specialized agents:

- **Profile Manager Agent** - Stores household profiles, restrictions, appliances, preferences
- **Recipe Generation Agent** - Generates candidate recipes with Gemini (API-integrated!)
- **Nutrition Compliance Agent** - Validates nutritional requirements & restrictions
- **Weekly Schedule Optimizer Agent** - Minimizes cooking time + maximizes ingredient reuse
- **Grocery List Agent** - Summarizes all ingredients into a clean weekly list

Agents communicate in a coordinated sequential pipeline with validation loops.

### 🔧 2. Tooling

MealMind includes a mix of custom, built-in, and OpenAPI tools:

**Custom Tools:**
- `nutrition_lookup` → Fetch nutritional data from USDA dataset
- `family_profile_store` → Add/edit family profiles
- `ingredient_cost_estimator` → Estimate weekly cost

**Built-In Tools:**
- Code execution → Calculate macros, compute grocery totals
- Google Search → Optional recipe substitution/availability

**MCP Tools:**
- Local storage, file writing

**Optional OpenAPI Tool:**
- Mocked recipe or nutrition API schema for expanded capabilities

### 🧵 3. Long-Running Operations *(Coming Soon)*

Weekly planning is a complex multi-step process. MealMind will use:
- `pause/resume` (via ADK Long-Running Operations)
- Stepwise planning: Breakfast → pause → Lunch → resume → Dinner → resume
- Looping until all constraints are satisfied

### 🧩 4. Sessions & Memory

The project uses:
- **InMemorySessionService** → Session-level meal generation
- **Memory Bank (Long-Term Memory)** → Stores:
  - Family profiles
  - Favorite recipes
  - Disliked ingredients
  - Health conditions
  - Past weekly plans (for context compaction)
- **Context Engineering** → Summarizes previous runs into compact facts

### 🔍 5. Observability

- Structured logging for each agent
- Tracing of decisions (why recipes were chosen or rejected)
- Metrics:
  - Constraint satisfaction %
  - Average cooking time per day
  - Recipes revised per plan

### 🧪 6. Agent Evaluation

MealMind includes a comprehensive evaluation test suite:

**Constraint Adherence Tests:**
- Allergen detection (ensures no allergens in recipes)
- Dietary restriction compliance (vegetarian, gluten-free, etc.)
- Health condition guidelines validation
- Cooking time constraint verification

**Nutrition Accuracy Tests:**
- Nutrition lookup accuracy
- Recipe nutrition calculation
- Calorie target validation
- Macro balance verification

**Optimization Tests:**
- Cooking time analysis
- Ingredient reuse efficiency
- Cost estimation accuracy
- Grocery list aggregation
- Budget compliance

**Run tests:**
```bash
pytest evaluation/ -v
```

### 🚀 7. Deployment & Notebooks

MealMind supports multiple interfaces:

**Jupyter Notebooks:**
- `notebooks/demo.ipynb` - Interactive demonstration
- `notebooks/evaluation.ipynb` - Test results with visualizations

**Deployment Options *(Coming Soon)*:**
- Streamlit front-end (demo UI)
- Flask API endpoint

---

## 🏗️ Architecture

```
User Input → Profile Manager Agent
          ↓
     Recipe Generation Agent
          ↓
   Nutrition Compliance Agent
          ↓ (Loop if needed)
   Weekly Schedule Optimizer
          ↓
     Grocery List Agent
          ↓
   Final Output: Weekly Meal Plan + Grocery List
```

---

## 📁 Project Structure

```
mealmind/
│
├── agents/
│   ├── profile_manager.py        # ✅ Implemented
│   ├── recipe_generator.py       # ✅ Implemented (Gemini-integrated!)
│   ├── nutrition_compliance.py   # ✅ Implemented
│   ├── schedule_optimizer.py     # ✅ Implemented
│   └── grocery_agent.py           # ✅ Implemented
│
├── tools/
│   ├── nutrition_lookup.py       # ✅ Implemented
│   ├── family_profile_store.py   # ✅ Implemented
│   ├── ingredient_cost_estimator.py  # ✅ Implemented
│   └── openapi_recipe_api.json   # ✅ Implemented
│
├── memory/
│   ├── long_term_memory.json     # ✅ Implemented
│   └── session_manager.py        # ✅ Implemented
│
├── utils/
│   └── logger.py                 # ✅ Implemented
│
├── evaluation/                   # ✅ Implemented
│   ├── __init__.py
│   ├── constraint_tests.py       # 6 constraint tests
│   ├── nutrition_accuracy_tests.py # 6 nutrition tests
│   └── optimization_tests.py     # 10 optimization tests
│
├── notebooks/                    # ✅ Implemented
│   ├── demo.ipynb                # Interactive demo
│   └── evaluation.ipynb          # Test visualization
│
├── app/                          # 🚧 Coming Soon
│   ├── streamlit_app.py
│   └── flask_api.py
│
├── config.py                     # ✅ Implemented
├── .env.example                  # ✅ Implemented
├── requirements.txt              # ✅ Implemented
└── README.md                     # ✅ This file
```

**Legend:**
- ✅ Implemented
- 🚧 Coming Soon

---

## 🧩 Example Use Case

**User Input:**
- 4 family members
- Member 1: PCOS-friendly, low-GI
- Member 2: Gluten-free
- Member 3: Vegetarian
- Member 4: Normal diet but prefers spicy food
- Shared constraint: Max 45 minutes/day cooking

**Output:**
- 7-day meal plan
- Unified grocery list
- Time-optimized cooking schedule
- All constraints validated

---

## 🛠️ Skills Demonstrated

- ✅ Multi-Agent Systems (5 sequential agents + loop validation)
- ✅ Custom Tools (nutrition, profiles, cost estimation)
- ✅ Google Gemini AI Integration (with automatic fallback)
- ✅ Sessions & Long-Term Memory (Memory Bank)
- ✅ Context Engineering (compaction, state management)
- ✅ Observability (structured logs, tracing, metrics)
- ✅ Agent Coordination & Orchestration
- 🚧 Long-Running Operations (pause/resume) - Optional
- 🚧 Agent Evaluation Suite - Optional
- 🚧 Deployment (Streamlit/Flask UI) - Optional

---

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Google AI API key (for Gemini integration)
- (Optional) USDA FoodData Central API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/mealmind.git
   cd mealmind
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Configure Google API key (Optional - enables Gemini):**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   ```
   
   Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey)
   
   **Note:** System works without API key using mock recipes!

---

## ▶️ Running the Agent

### Python Script (Current)

```python
from agents.profile_manager import profile_manager
from agents.recipe_generator import recipe_generator

# Create household profile
household = profile_manager.create_household_profile(
    household_id="family_01",
    cooking_time_max=45,
    appliances=["oven", "stove", "microwave"],
    cuisine_preferences=["Mediterranean", "Asian"]
)

# Add family members
profile_manager.add_family_member(
    household_id="family_01",
    name="Alice",
    health_conditions=["PCOS"],
    dietary_restrictions=["low-GI"]
)

profile_manager.add_family_member(
    household_id="family_01",
    name="Bob",
    dietary_restrictions=["gluten-free"]
)

# Generate planning context
context = profile_manager.generate_planning_context("family_01")
constraints = profile_manager.get_all_constraints("family_01")

# Generate weekly meal plan
weekly_plan = recipe_generator.generate_weekly_meals(
    planning_context=context,
    constraints=constraints,
    days=7
)

print(f"Generated {len(weekly_plan)} days of meals!")
```

### Streamlit UI *(Coming Soon)*
```bash
streamlit run app/streamlit_app.py
```

### Flask API *(Coming Soon)*
```bash
python app/flask_api.py
```

### Kaggle Notebook *(Coming Soon)*
Open `notebooks/demo.ipynb` and run all cells.

---

## 🧪 Testing

### Run Evaluation Suite
```bash
# Run all tests
pytest evaluation/ -v

# Run specific test category
pytest evaluation/constraint_tests.py -v
pytest evaluation/nutrition_accuracy_tests.py -v
pytest evaluation/optimization_tests.py -v

# Run with coverage
pytest --cov=. evaluation/ --cov-report=html
```

### Interactive Notebooks
```bash
# Launch Jupyter
jupyter notebook notebooks/

# Or use JupyterLab
jupyter lab notebooks/
```

**Notebooks include:**
- `demo.ipynb` - Step-by-step demonstration
- `evaluation.ipynb` - Test results with charts

---

## 📊 Evaluation Metrics

The evaluation suite tests:

1. **Constraint Adherence** - Verifies allergies and restrictions are respected
2. **Nutrition Accuracy** - Compares calculated vs. actual nutritional values
3. **Cooking Time Optimization** - Ensures time constraints are met
4. **Ingredient Reuse** - Measures efficiency of grocery planning
5. **Cost Estimation** - Validates budget adherence

---

## 🧭 Roadmap

### Phase 1: Foundation ✅
- [x] Project setup and configuration
- [x] Core tools development
- [x] Memory and session management
- [x] Profile Manager Agent
- [x] Recipe Generator Agent

### Phase 2: Core Agents ✅
- [x] Nutrition Compliance Agent
- [x] Schedule Optimizer Agent
- [x] Grocery List Agent

### Phase 3: Orchestration ✅
- [x] Multi-agent communication
- [x] Agent coordination workflow
- [x] Agent loop with retry logic

### Phase 4: Evaluation 🚧
- [ ] Constraint adherence tests
- [ ] Nutrition accuracy tests
- [ ] Optimization benchmarks

### Phase 5: Deployment 🚧
- [ ] Streamlit UI
- [ ] Flask API
- [ ] Kaggle notebook demo

### Future Enhancements 💡
- [ ] Cost optimization agent
- [ ] Automatic health profile updates
- [ ] Recipe image generation
- [ ] Multilingual recipe support
- [ ] Family feedback loop (reinforcement learning)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google AI** for Gemini API and ADK framework
- **Kaggle** for the Google Intensive program
- **USDA** for FoodData Central API
- All contributors and testers

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ using Google ADK + Gemini**
