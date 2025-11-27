"""Profile Manager Agent - Manages household and family member profiles."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from tools import profile_store
from memory import memory_bank
from utils import get_logger

logger = get_logger(__name__)


class ProfileManagerAgent:
    """Agent responsible for managing family profiles and constraints."""
    
    def __init__(self):
        """Initialize the Profile Manager Agent."""
        self.profile_store = profile_store
        self.memory = memory_bank
        logger.info("profile_manager_agent_initialized")
    
    def create_household_profile(
        self,
        household_id: str,
        cooking_time_max: int = 45,
        appliances: Optional[List[str]] = None,
        budget_weekly: Optional[float] = None,
        cuisine_preferences: Optional[List[str]] = None
    ) -> Dict:
        """Create a new household profile.
        
        Args:
            household_id: Unique household identifier
            cooking_time_max: Maximum cooking time per day in minutes
            appliances: Available kitchen appliances
            budget_weekly: Weekly grocery budget
            cuisine_preferences: Preferred cuisines
            
        Returns:
            Created household profile
        """
        logger.info(
            "creating_household_profile",
            household_id=household_id,
            cooking_time_max=cooking_time_max
        )
        
        profile = self.profile_store.create_household(
            household_id=household_id,
            cooking_time_max_minutes=cooking_time_max,
            appliances=appliances,
            budget_weekly=budget_weekly
        )
        
        # Update cuisine preferences if provided
        if cuisine_preferences:
            profile.cuisine_preferences = cuisine_preferences
            self.profile_store._save_profiles()
        
        logger.info("household_profile_created", household_id=household_id)
        return profile.model_dump()
    
    def add_family_member(
        self,
        household_id: str,
        name: str,
        age: Optional[int] = None,
        health_conditions: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        preferences: Optional[List[str]] = None,
        dislikes: Optional[List[str]] = None,
        calorie_target: Optional[int] = None
    ) -> Dict:
        """Add a family member to a household.
        
        Args:
            household_id: Household identifier
            name: Member name
            age: Member age
            health_conditions: Health conditions (diabetes, PCOS, etc.)
            allergies: Food allergies
            dietary_restrictions: Dietary restrictions (vegan, gluten-free, etc.)
            preferences: Food preferences
            dislikes: Disliked foods
            calorie_target: Daily calorie target
            
        Returns:
            Created family member profile
        """
        logger.info(
            "adding_family_member",
            household_id=household_id,
            name=name,
            health_conditions=health_conditions,
            allergies=allergies
        )
        
        member = self.profile_store.add_member(
            household_id=household_id,
            name=name,
            age=age,
            health_conditions=health_conditions,
            allergies=allergies,
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
            dislikes=dislikes,
            calorie_target=calorie_target
        )
        
        # Store dislikes in long-term memory
        if dislikes:
            for dislike in dislikes:
                self.memory.add_disliked_ingredient(household_id, dislike)
        
        logger.info("family_member_added", household_id=household_id, name=name)
        return member.model_dump()
    
    def get_household_profile(self, household_id: str) -> Optional[Dict]:
        """Get complete household profile.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Household profile with all members
        """
        profile = self.profile_store.get_household(household_id)
        if profile:
            return profile.model_dump()
        return None
    
    def get_all_constraints(self, household_id: str) -> Dict:
        """Get all dietary constraints for the household.
        
        This aggregates all constraints from all family members to ensure
        the meal plan respects everyone's needs.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Dictionary with aggregated constraints
        """
        logger.info("getting_household_constraints", household_id=household_id)
        
        constraints = self.profile_store.get_all_constraints(household_id)
        
        # Enrich with health condition guidelines from memory
        health_guidelines = {}
        for condition in constraints.get("health_conditions", []):
            guidelines = self.memory.get_health_condition_guidelines(condition)
            health_guidelines[condition] = guidelines
        
        constraints["health_guidelines"] = health_guidelines
        
        # Add historical dislikes from memory
        memory_dislikes = self.memory.get_disliked_ingredients(household_id)
        constraints["disliked_ingredients_memory"] = memory_dislikes
        
        logger.info(
            "constraints_retrieved",
            household_id=household_id,
            allergies_count=len(constraints.get("allergies", [])),
            restrictions_count=len(constraints.get("dietary_restrictions", []))
        )
        
        return constraints
    
    def get_member_specific_needs(self, household_id: str, member_name: str) -> Dict:
        """Get specific dietary needs for a single member.
        
        Args:
            household_id: Household identifier
            member_name: Member name
            
        Returns:
            Member's specific needs and constraints
        """
        member = self.profile_store.get_member(household_id, member_name)
        if not member:
            return {}
        
        needs = {
            "allergies": member.allergies,
            "dietary_restrictions": member.dietary_restrictions,
            "health_conditions": member.health_conditions,
            "preferences": member.preferences,
            "dislikes": member.dislikes,
            "calorie_target": member.calorie_target
        }
        
        # Add health condition guidelines
        health_guidelines = {}
        for condition in member.health_conditions:
            guidelines = self.memory.get_health_condition_guidelines(condition)
            health_guidelines[condition] = guidelines
        
        needs["health_guidelines"] = health_guidelines
        
        return needs
    
    def validate_profile_completeness(self, household_id: str) -> Dict:
        """Validate that the household profile is complete enough for meal planning.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Dictionary with validation status and missing fields
        """
        profile = self.profile_store.get_household(household_id)
        
        if not profile:
            return {
                "valid": False,
                "errors": ["Household profile not found"]
            }
        
        errors = []
        warnings = []
        
        # Check if household has members
        if not profile.members:
            errors.append("No family members added to household")
        
        # Check each member
        for name, member in profile.members.items():
            if not member.health_conditions and not member.allergies and not member.dietary_restrictions:
                warnings.append(f"{name} has no dietary constraints specified")
        
        # Check cooking constraints
        if profile.cooking_time_max_minutes <= 0:
            errors.append("Cooking time must be greater than 0")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "member_count": len(profile.members)
        }
    
    def generate_planning_context(self, household_id: str) -> Dict:
        """Generate a comprehensive context for meal planning.
        
        This creates a structured summary of the household that can be used
        by other agents in the planning process.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Comprehensive planning context
        """
        logger.info("generating_planning_context", household_id=household_id)
        
        profile = self.profile_store.get_household(household_id)
        if not profile:
            raise ValueError(f"Household {household_id} not found")
        
        constraints = self.get_all_constraints(household_id)
        
        # Build member summaries
        member_summaries = []
        for name, member in profile.members.items():
            summary = {
                "name": name,
                "age": member.age,
                "health_conditions": member.health_conditions,
                "allergies": member.allergies,
                "dietary_restrictions": member.dietary_restrictions,
                "preferences": member.preferences,
                "dislikes": member.dislikes,
                "calorie_target": member.calorie_target
            }
            member_summaries.append(summary)
        
        # Get long-term memory context
        memory_context = self.memory.compact_context(household_id)
        
        context = {
            "household_id": household_id,
            "members": member_summaries,
            "member_count": len(profile.members),
            "constraints": constraints,
            "cooking_time_max": profile.cooking_time_max_minutes,
            "appliances": profile.shared_appliances,
            "budget_weekly": profile.budget_weekly,
            "cuisine_preferences": profile.cuisine_preferences,
            "memory_context": memory_context
        }
        
        logger.info("planning_context_generated", household_id=household_id)
        return context


# Create global instance
profile_manager = ProfileManagerAgent()
