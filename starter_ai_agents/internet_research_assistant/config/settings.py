import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))

    # Search
    max_search_results: int = field(
        default_factory=lambda: int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    )
    search_timeout: int = field(
        default_factory=lambda: int(os.getenv("SEARCH_TIMEOUT", "10"))
    )
    max_concurrent_searches: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_SEARCHES", "3"))
    )

    # Cache
    cache_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    )
    cache_max_size: int = field(
        default_factory=lambda: int(os.getenv("CACHE_MAX_SIZE", "100"))
    )

    # Database
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "research_assistant.db")
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = field(
        default_factory=lambda: os.getenv("LOG_FILE", "research_assistant.log")
    )

    # UI
    app_title: str = "Internet Research Assistant"
    app_icon: str = "🔍"
    max_history_display: int = 50

    # Retry
    max_retries: int = 3
    retry_delay: float = 1.0

    def validate(self) -> bool:
        return bool(self.openai_api_key)
