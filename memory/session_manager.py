"""Session management for MealMind using Google ADK."""
import json
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from utils import get_logger

logger = get_logger(__name__)


class SessionData(BaseModel):
    """Session data structure."""
    session_id: str
    household_id: Optional[str] = None
    created_at: str
    last_active: str
    context: Dict[str, Any] = {}
    conversation_history: List[Dict[str, str]] = []


class MemoryBank:
    """Long-term memory storage for MealMind."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the memory bank.
        
        Args:
            storage_path: Path to store long-term memory
        """
        if storage_path is None:
            storage_path = Path(__file__).parent / "long_term_memory.json"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory: Dict[str, Any] = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.memory = json.load(f)
                logger.info("memory_loaded", keys=list(self.memory.keys()))
            except Exception as e:
                logger.error("memory_load_error", error=str(e))
                self.memory = self._initialize_memory_structure()
        else:
            self.memory = self._initialize_memory_structure()
            self._save_memory()
    
    def _initialize_memory_structure(self) -> Dict:
        """Initialize empty memory structure.
        
        Returns:
            Empty memory dictionary with proper structure
        """
        return {
            "households": {},
            "favorite_recipes": {},
            "disliked_ingredients": {},
            "historical_plans": [],
            "learned_preferences": {},
            "health_condition_mappings": {
                "diabetes": {
                    "avoid": ["sugar", "white bread", "candy", "soda"],
                    "prefer": ["whole grains", "vegetables", "lean protein"]
                },
                "PCOS": {
                    "avoid": ["refined carbs", "sugary foods"],
                    "prefer": ["low-GI foods", "lean protein", "vegetables"]
                },
                "high blood pressure": {
                    "avoid": ["salt", "processed foods", "fatty meats"],
                    "prefer": ["low sodium", "vegetables", "whole grains"]
                },
                "gluten intolerance": {
                    "avoid": ["wheat", "barley", "rye"],
                    "prefer": ["rice", "quinoa", "gluten-free grains"]
                }
            }
        }
    
    def _save_memory(self):
        """Save memory to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
            logger.info("memory_saved")
        except Exception as e:
            logger.error("memory_save_error", error=str(e))
    
    def store_meal_plan(self, household_id: str, plan: Dict):
        """Store a weekly meal plan in memory.
        
        Args:
            household_id: Household identifier
            plan: Meal plan dictionary
        """
        if "historical_plans" not in self.memory:
            self.memory["historical_plans"] = []
        
        plan_entry = {
            "household_id": household_id,
            "created_at": datetime.now().isoformat(),
            "plan": plan
        }
        
        self.memory["historical_plans"].append(plan_entry)
        
        # Keep only last 10 plans per household
        household_plans = [p for p in self.memory["historical_plans"] 
                          if p["household_id"] == household_id]
        if len(household_plans) > 10:
            # Remove oldest
            for old_plan in household_plans[:-10]:
                self.memory["historical_plans"].remove(old_plan)
        
        self._save_memory()
        logger.info("meal_plan_stored", household_id=household_id)
    
    def get_favorite_recipes(self, household_id: str) -> List[Dict]:
        """Get favorite recipes for a household.
        
        Args:
            household_id: Household identifier
            
        Returns:
            List of favorite recipes
        """
        return self.memory.get("favorite_recipes", {}).get(household_id, [])
    
    def add_favorite_recipe(self, household_id: str, recipe: Dict):
        """Add a recipe to favorites.
        
        Args:
            household_id: Household identifier
            recipe: Recipe dictionary
        """
        if "favorite_recipes" not in self.memory:
            self.memory["favorite_recipes"] = {}
        
        if household_id not in self.memory["favorite_recipes"]:
            self.memory["favorite_recipes"][household_id] = []
        
        self.memory["favorite_recipes"][household_id].append(recipe)
        self._save_memory()
        logger.info("favorite_recipe_added", household_id=household_id)
    
    def get_disliked_ingredients(self, household_id: str) -> List[str]:
        """Get disliked ingredients for a household.
        
        Args:
            household_id: Household identifier
            
        Returns:
            List of disliked ingredients
        """
        return self.memory.get("disliked_ingredients", {}).get(household_id, [])
    
    def add_disliked_ingredient(self, household_id: str, ingredient: str):
        """Add an ingredient to the dislike list.
        
        Args:
            household_id: Household identifier
            ingredient: Ingredient name
        """
        if "disliked_ingredients" not in self.memory:
            self.memory["disliked_ingredients"] = {}
        
        if household_id not in self.memory["disliked_ingredients"]:
            self.memory["disliked_ingredients"][household_id] = []
        
        if ingredient not in self.memory["disliked_ingredients"][household_id]:
            self.memory["disliked_ingredients"][household_id].append(ingredient)
            self._save_memory()
            logger.info("disliked_ingredient_added", household_id=household_id, ingredient=ingredient)
    
    def get_health_condition_guidelines(self, condition: str) -> Dict:
        """Get dietary guidelines for a health condition.
        
        Args:
            condition: Health condition name
            
        Returns:
            Dictionary with 'avoid' and 'prefer' lists
        """
        condition_lower = condition.lower()
        return self.memory.get("health_condition_mappings", {}).get(
            condition_lower,
            {"avoid": [], "prefer": []}
        )
    
    def get_recent_plans(self, household_id: str, limit: int = 3) -> List[Dict]:
        """Get recent meal plans for context.
        
        Args:
            household_id: Household identifier
            limit: Maximum number of plans to return
            
        Returns:
            List of recent meal plans
        """
        household_plans = [
            p for p in self.memory.get("historical_plans", [])
            if p["household_id"] == household_id
        ]
        return household_plans[-limit:]
    
    def compact_context(self, household_id: str) -> Dict:
        """Create a compact context summary for efficient LLM prompts.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Compacted context dictionary
        """
        recent_plans = self.get_recent_plans(household_id, limit=2)
        
        # Extract commonly used ingredients
        ingredient_frequency = {}
        for plan_entry in recent_plans:
            # Access the actual plan data (weekly_plan is the list of days)
            plan = plan_entry.get("plan", {})
            weekly_plan = plan.get("weekly_plan", [])
            
            for day in weekly_plan:
                for meal in day.get("meals", []):
                    for ingredient in meal.get("ingredients", []):
                        name = ingredient.get("name", "")
                        if name:
                            ingredient_frequency[name] = ingredient_frequency.get(name, 0) + 1
        
        common_ingredients = sorted(
            ingredient_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "favorite_recipes_count": len(self.get_favorite_recipes(household_id)),
            "common_ingredients": [ing[0] for ing in common_ingredients],
            "disliked_ingredients": self.get_disliked_ingredients(household_id),
            "plans_generated": len(recent_plans)
        }


class SessionManager:
    """Manage user sessions for MealMind."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, SessionData] = {}
        self.memory_bank = MemoryBank()
    
    def create_session(self, session_id: str, household_id: Optional[str] = None) -> SessionData:
        """Create a new session.
        
        Args:
            session_id: Unique session identifier
            household_id: Optional household identifier
            
        Returns:
            Created session data
        """
        now = datetime.now().isoformat()
        session = SessionData(
            session_id=session_id,
            household_id=household_id,
            created_at=now,
            last_active=now
        )
        
        self.sessions[session_id] = session
        logger.info("session_created", session_id=session_id)
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get an existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            session.last_active = datetime.now().isoformat()
        return session
    
    def update_session_context(self, session_id: str, context_updates: Dict):
        """Update session context.
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
        """
        session = self.get_session(session_id)
        if session:
            session.context.update(context_updates)
            logger.info("session_context_updated", session_id=session_id)
    
    def add_to_conversation(self, session_id: str, role: str, message: str):
        """Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Role (user or assistant)
            message: Message content
        """
        session = self.get_session(session_id)
        if session:
            session.conversation_history.append({
                "role": role,
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            logger.info("conversation_updated", session_id=session_id, role=role)
    
    def get_session_context(self, session_id: str) -> Dict:
        """Get complete session context including long-term memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Combined context dictionary
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        context = session.context.copy()
        
        # Add long-term memory context if household_id is set
        if session.household_id:
            context["long_term_memory"] = self.memory_bank.compact_context(session.household_id)
        
        return context
    
    def end_session(self, session_id: str):
        """End a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("session_ended", session_id=session_id)


# Create global instances
session_manager = SessionManager()
memory_bank = session_manager.memory_bank
