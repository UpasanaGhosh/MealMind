# 🌱 MealMind: A Multi-Agent Family Meal Planning Concierge
An Agentic Meal Planner Using Google ADK + Gemini | Kaggle X Google Intensive Capstone Project

### 🧭  Overview
MealMind is an intelligent multi-agent meal planning assistant designed to create weekly meal plans for individuals and families, especially when multiple people have overlapping or conflicting dietary needs.

Unlike typical meal apps that serve a single user, MealMind uses LLM-driven reasoning, multi-agent collaboration, and structured tools to:

- Generate a 7-day meal plan for a whole family
- Respect health conditions (e.g., diabetes, PCOS, high BP)
- Consider allergies, dislikes, and preferences
- Optimize for cooking time and shared ingredients
- Produce a grocery list
- Track long-term preferences and constraints

This project demonstrates key concepts from the Google ADK + Gemini Kaggle Intensive, including multi-agent systems, tool integration, memory, observability, agent loops, and evaluation.

### ⭐️  Key Features
#### 🧠 1. Multi-Agent System

MealMind is built using multiple specialized agents:

- <b> Profile Manager Agent </b> <br/>
  Stores household profiles, restrictions, appliances, preferences.<br/>
  
- <b>Recipe Generation Agent</b> <br/>
  Generates candidate recipes with Gemini.<br/>
  
- <b>Nutrition Compliance Agent</b> <br/>
  Validates nutritional requirements & restrictions.<br/>
  
- <b>Weekly Schedule Optimizer Agent</b> <br/>
  Minimizes cooking time + maximizes ingredient reuse.<br/>
  
- <b>Grocery List Agent</b> <br/>
  Summarizes all ingredients into a clean weekly list.<br/>

Agents communicate using Google ADK A2A protocol.

#### 🔧 2. Tooling

MealMind includes a mix of custom, built-in, and OpenAPI tools.

Custom Tools

nutrition_lookup → Fetch nutritional data from USDA dataset

family_profile_store → Add/edit family profiles

ingredient_cost_estimator → Estimate weekly cost

Built-In Tools

Code execution → Calculate macros, compute grocery totals

Google Search → Optional recipe substitution/availability

MCP Tools → Local storage, file writing

Optional OpenAPI Tool

Mocked recipe or nutrition API schema for expanded capabilities.

#### 🧵 3. Long-Running Operations

Weekly planning is a complex multi-step process. MealMind uses:

pause/resume (via ADK Long-Running Operations)

Stepwise planning:

Breakfast → pause

Lunch → resume

Dinner → resume

Looping until all constraints are satisfied

#### 🧩 4. Sessions & Memory

The project uses:

InMemorySessionService → Session-level meal generation

Memory Bank (Long-Term Memory) →
Stores:

Family profiles

Favorite recipes

Disliked ingredients

Health conditions

Past weekly plans (for context compaction)

Context Engineering

Summarizes previous runs into compact facts

Makes the agent efficient across sessions

#### 🔍 5. Observability

Structured logging for each agent

Tracing of decisions (why recipes were chosen or rejected)

Metrics:

Constraint satisfaction %

Average cooking time per day

Recipes revised per plan

#### 🧪 6. Agent Evaluation

MealMind includes evaluation tests for:

Constraint adherence (allergies, conditions)

Nutrition accuracy (verified via tool calls)

Cooking-time optimization

Ingredient duplication reduction

Evaluation notebooks are included in the repo.

#### 🚀 7. Deployment

MealMind supports multiple deployment methods:

Streamlit front-end (demo UI)

Flask API endpoint

Notebook-based agent run on Kaggle

### 🏗️ Architecture
flowchart TD
    A[User Input: Family Members, Health Conditions, Preferences] --> B(Profile Manager Agent)

    B -->|Profiles Stored in Memory Bank| C(Recipe Generation Agent)
    C --> D(Nutrition Compliance Agent)

    D -->|Loop Until All Criteria Met| C

    D --> E(Weekly Schedule Optimizer)
    E --> F(Grocery List Agent)

    F --> G[Final Output: Weekly Meal Plan + Grocery List]

📁 Project Structure
mealmind/
│
├── agents/
│   ├── profile_manager.py
│   ├── recipe_generator.py
│   ├── nutrition_compliance.py
│   ├── schedule_optimizer.py
│   └── grocery_agent.py
│
├── tools/
│   ├── nutrition_lookup.py
│   ├── family_profile_store.py
│   ├── ingredient_cost_estimator.py
│   └── openapi_recipe_api.json
│
├── memory/
│   ├── long_term_memory.json
│   └── session_manager.py
│
├── evaluation/
│   ├── constraint_tests.py
│   ├── nutrition_accuracy_tests.py
│   └── optimization_tests.py
│
├── notebooks/
│   ├── demo.ipynb
│   └── evaluation.ipynb
│
├── app/
│   ├── streamlit_app.py
│   └── flask_api.py
│
├── README.md
└── requirements.txt

🧩 Example Use Case
User Input:

4 family members

Member 1: PCOS-friendly, low-GI

Member 2: Gluten-free

Member 3: Vegetarian

Member 4: Normal diet but prefers spicy food

Shared constraint: Max 45 minutes/day cooking

Output:

7-day meal plan

Unified grocery list

Time-optimized cooking schedule

All constraints validated

🛠️ Skills Demonstrated

✔ Multi-Agent Systems (parallel, sequential, loop agents)
✔ MCP & Custom Tools
✔ Google Search & Built-In Tools
✔ Long-Running Operations (pause/resume)
✔ Sessions & Long-Term Memory (Memory Bank)
✔ Context Engineering (compaction, state management)
✔ Observability (logs, tracing, metrics)
✔ Agent Evaluation Suite
✔ A2A Protocol
✔ Deployment (API + UI)

📦 Installation
git clone https://github.com/yourusername/mealmind.git
cd mealmind
pip install -r requirements.txt

▶️ Running the Agent
Streamlit UI
streamlit run app/streamlit_app.py

Flask API
python app/flask_api.py

Kaggle Notebook

Open notebooks/demo.ipynb and run all cells.

🧭 Roadmap

 Add cost optimization

 Add automatic health profile updates

 Add recipe image generation

 Support for multilingual recipes

 Family feedback loop (reinforcement)

🤝 Contributing

PRs and feedback are welcome!
Open an issue to discuss improvements or contribute new agents/tools.

📜 License

MIT License
