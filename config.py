"""Configuration management for MealMind."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    USDA_API_KEY = os.getenv("USDA_API_KEY", "")
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # Model Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
    
    # Memory Settings
    PROJECT_ROOT = Path(__file__).parent
    MEMORY_PERSISTENCE_PATH = os.getenv(
        "MEMORY_PERSISTENCE_PATH",
        str(PROJECT_ROOT / "memory" / "long_term_memory.json")
    )
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    
    # Cost Estimation (default prices per kg)
    DEFAULT_PROTEIN_COST = float(os.getenv("DEFAULT_PROTEIN_COST", "15.00"))
    DEFAULT_VEGETABLE_COST = float(os.getenv("DEFAULT_VEGETABLE_COST", "5.00"))
    DEFAULT_GRAIN_COST = float(os.getenv("DEFAULT_GRAIN_COST", "3.00"))
    DEFAULT_DAIRY_COST = float(os.getenv("DEFAULT_DAIRY_COST", "8.00"))
    
    # USDA FoodData Central API
    USDA_API_URL = "https://api.nal.usda.gov/fdc/v1"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required. Please set it in .env file.")
        return True

# Validate configuration on import
config = Config()
