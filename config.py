import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Global configuration for the JARVIS Personal AI Assistant."""
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    
    # Base Paths
    BASE_DIR: Path = Path(__file__).parent.resolve()
    DATA_DIR: Path = BASE_DIR / "data"
    
    # File Paths
    MEMORY_FILE: Path = DATA_DIR / "memory.json"
    REMINDERS_FILE: Path = DATA_DIR / "reminders.json"
    
    # Voice Configuration
    WAKE_WORD: str = os.getenv("WAKE_WORD", "Hey Nova") # Or "Hey Jarvis"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing from environment variables. Please check your .env file.")

config = Config()
