"""Family profile storage and management tool."""
import json
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from utils import get_logger

logger = get_logger(__name__)


class FamilyMember(BaseModel):
    """Profile for a family member."""
    name: str
    age: Optional[int] = None
    health_conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    calorie_target: Optional[int] = None
    macro_targets: Optional[Dict[str, float]] = None  # protein, carbs, fat percentages


class HouseholdProfile(BaseModel):
    """Complete household profile."""
    household_id: str
    members: Dict[str, FamilyMember] = Field(default_factory=dict)
    shared_appliances: List[str] = Field(default_factory=list)
    cooking_time_max_minutes: int = 45
    budget_weekly: Optional[float] = None
    cuisine_preferences: List[str] = Field(default_factory=list)
    meal_count_per_day: int = 3
    

class FamilyProfileStore:
    """Store and manage family profiles."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the profile store.
        
        Args:
            storage_path: Path to store profiles (default: memory/profiles.json)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "memory" / "profiles.json"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, HouseholdProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load profiles from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for household_id, profile_data in data.items():
                        self.profiles[household_id] = HouseholdProfile(**profile_data)
                logger.info("profiles_loaded", count=len(self.profiles))
            except Exception as e:
                logger.error("profiles_load_error", error=str(e))
                self.profiles = {}
        else:
            logger.info("no_existing_profiles")
    
    def _save_profiles(self):
        """Save profiles to disk."""
        try:
            data = {
                household_id: profile.model_dump()
                for household_id, profile in self.profiles.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("profiles_saved", count=len(self.profiles))
        except Exception as e:
            logger.error("profiles_save_error", error=str(e))
    
    def create_household(
        self,
        household_id: str,
        cooking_time_max_minutes: int = 45,
        appliances: Optional[List[str]] = None,
        budget_weekly: Optional[float] = None
    ) -> HouseholdProfile:
        """Create a new household profile.
        
        Args:
            household_id: Unique identifier for the household
            cooking_time_max_minutes: Maximum cooking time per day
            appliances: List of available appliances
            budget_weekly: Weekly budget for groceries
            
        Returns:
            Created household profile
        """
        if household_id in self.profiles:
            logger.warning("household_exists", household_id=household_id)
            return self.profiles[household_id]
        
        profile = HouseholdProfile(
            household_id=household_id,
            cooking_time_max_minutes=cooking_time_max_minutes,
            shared_appliances=appliances or [],
            budget_weekly=budget_weekly
        )
        
        self.profiles[household_id] = profile
        self._save_profiles()
        
        logger.info("household_created", household_id=household_id)
        return profile
    
    def add_member(
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
    ) -> FamilyMember:
        """Add a family member to a household.
        
        Args:
            household_id: Household identifier
            name: Member name
            age: Member age
            health_conditions: List of health conditions (e.g., "diabetes", "PCOS")
            allergies: List of allergies
            dietary_restrictions: List of dietary restrictions (e.g., "vegan", "gluten-free")
            preferences: List of food preferences
            dislikes: List of disliked foods
            calorie_target: Daily calorie target
            
        Returns:
            Created family member profile
        """
        if household_id not in self.profiles:
            raise ValueError(f"Household {household_id} does not exist")
        
        member = FamilyMember(
            name=name,
            age=age,
            health_conditions=health_conditions or [],
            allergies=allergies or [],
            dietary_restrictions=dietary_restrictions or [],
            preferences=preferences or [],
            dislikes=dislikes or [],
            calorie_target=calorie_target
        )
        
        self.profiles[household_id].members[name] = member
        self._save_profiles()
        
        logger.info("member_added", household_id=household_id, member=name)
        return member
    
    def get_household(self, household_id: str) -> Optional[HouseholdProfile]:
        """Get a household profile.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Household profile if found, None otherwise
        """
        return self.profiles.get(household_id)
    
    def get_member(self, household_id: str, member_name: str) -> Optional[FamilyMember]:
        """Get a specific family member profile.
        
        Args:
            household_id: Household identifier
            member_name: Member name
            
        Returns:
            Family member profile if found, None otherwise
        """
        household = self.get_household(household_id)
        if household:
            return household.members.get(member_name)
        return None
    
    def update_member(
        self,
        household_id: str,
        member_name: str,
        **updates
    ) -> Optional[FamilyMember]:
        """Update a family member profile.
        
        Args:
            household_id: Household identifier
            member_name: Member name
            **updates: Fields to update
            
        Returns:
            Updated family member profile if found, None otherwise
        """
        member = self.get_member(household_id, member_name)
        if not member:
            logger.warning("member_not_found", household_id=household_id, member=member_name)
            return None
        
        for key, value in updates.items():
            if hasattr(member, key):
                setattr(member, key, value)
        
        self._save_profiles()
        logger.info("member_updated", household_id=household_id, member=member_name)
        return member
    
    def list_households(self) -> List[str]:
        """List all household IDs.
        
        Returns:
            List of household IDs
        """
        return list(self.profiles.keys())
    
    def delete_household(self, household_id: str) -> bool:
        """Delete a household profile.
        
        Args:
            household_id: Household identifier
            
        Returns:
            True if deleted, False if not found
        """
        if household_id in self.profiles:
            del self.profiles[household_id]
            self._save_profiles()
            logger.info("household_deleted", household_id=household_id)
            return True
        return False
    
    def get_all_constraints(self, household_id: str) -> Dict[str, List[str]]:
        """Get all dietary constraints for a household.
        
        Args:
            household_id: Household identifier
            
        Returns:
            Dictionary with combined constraints
        """
        household = self.get_household(household_id)
        if not household:
            return {}
        
        all_allergies = set()
        all_restrictions = set()
        all_conditions = set()
        all_dislikes = set()
        
        for member in household.members.values():
            all_allergies.update(member.allergies)
            all_restrictions.update(member.dietary_restrictions)
            all_conditions.update(member.health_conditions)
            all_dislikes.update(member.dislikes)
        
        return {
            "allergies": list(all_allergies),
            "dietary_restrictions": list(all_restrictions),
            "health_conditions": list(all_conditions),
            "dislikes": list(all_dislikes)
        }


# Create global instance
profile_store = FamilyProfileStore()


# Tool functions for agent use
def create_household_profile(
    household_id: str,
    cooking_time_max: int = 45,
    appliances: Optional[List[str]] = None
) -> Dict:
    """Create a new household profile.
    
    Args:
        household_id: Unique identifier for the household
        cooking_time_max: Maximum cooking time per day in minutes
        appliances: List of available appliances
    
    Returns:
        Created household profile as dictionary
    """
    profile = profile_store.create_household(household_id, cooking_time_max, appliances)
    return profile.model_dump()


def add_family_member(
    household_id: str,
    name: str,
    health_conditions: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    dietary_restrictions: Optional[List[str]] = None,
    preferences: Optional[List[str]] = None,
    dislikes: Optional[List[str]] = None
) -> Dict:
    """Add a family member to a household.
    
    Args:
        household_id: Household identifier
        name: Member name
        health_conditions: List of health conditions
        allergies: List of allergies
        dietary_restrictions: List of dietary restrictions
        preferences: List of food preferences
        dislikes: List of disliked foods
    
    Returns:
        Created family member profile as dictionary
    """
    member = profile_store.add_member(
        household_id, name, None,
        health_conditions, allergies, dietary_restrictions,
        preferences, dislikes
    )
    return member.model_dump()


def get_household_constraints(household_id: str) -> Dict:
    """Get all dietary constraints for a household.
    
    Args:
        household_id: Household identifier
    
    Returns:
        Dictionary with all constraints
    """
    return profile_store.get_all_constraints(household_id)
