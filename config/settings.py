"""
Configuration management for Internet Research Assistant
"""
import os
from dotenv import load_dotenv
from enum import Enum
from typing import Optional

load_dotenv()

class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

class CacheType(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"
    SQLITE = "sqlite"

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # LLM Provider
    LLM_PROVIDER: LLMProvider = LLMProvider(os.getenv("LLM_PROVIDER", "openai"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///research_assistant.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    
    # Cache Configuration
    CACHE_TYPE: CacheType = CacheType(os.getenv("CACHE_TYPE", "memory"))
    CACHE_REDIS_URL: str = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Search Configuration
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))
    SEARCH_MAX_RESULTS: int = int(os.getenv("SEARCH_MAX_RESULTS", "10"))
    SEARCH_CONCURRENT_REQUESTS: int = int(os.getenv("SEARCH_CONCURRENT_REQUESTS", "3"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/research_assistant.log")
    
    # Streamlit Configuration
    STREAMLIT_THEME: str = os.getenv("STREAMLIT_THEME", "dark")
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Feature Flags
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    ENABLE_PERSISTENCE: bool = os.getenv("ENABLE_PERSISTENCE", "true").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ENABLE_CONFIDENCE_SCORING: bool = os.getenv("ENABLE_CONFIDENCE_SCORING", "true").lower() == "true"

settings = Settings()
