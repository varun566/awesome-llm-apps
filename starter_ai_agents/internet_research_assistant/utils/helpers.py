import hashlib
import json
import re
import time
from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)


def make_cache_key(query: str) -> str:
    """Create a deterministic cache key from a query string."""
    normalized = query.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def timer(func):
    """Decorator that logs execution time."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"{func.__name__} completed in {elapsed:.1f} ms")
        return result

    return wrapper


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length, adding ellipsis when trimmed."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "…"


def sanitize_query(query: str) -> str:
    """Remove potentially harmful characters from a search query."""
    query = re.sub(r"--+", " ", query)            # SQL comment sequences
    query = re.sub(r"[<>\"';&|`$]", " ", query)
    return " ".join(query.split())


def format_sources(sources: list) -> str:
    """Format a list of source dicts into a readable markdown string."""
    if not sources:
        return "_No sources available._"
    lines = []
    for i, src in enumerate(sources, 1):
        title = src.get("title", "Untitled")
        url = src.get("url", "")
        snippet = truncate_text(src.get("snippet", ""), 200)
        lines.append(f"**{i}. [{title}]({url})**\n{snippet}")
    return "\n\n".join(lines)


def extract_json(text: str) -> Any:
    """Extract the first JSON object or array found in a string."""
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def score_confidence(sources: list, answer: str) -> float:
    """Heuristic confidence score [0, 1] based on source count and answer length."""
    if not sources or not answer:
        return 0.0
    source_score = min(len(sources) / 5.0, 1.0) * 0.5
    length_score = min(len(answer) / 500.0, 1.0) * 0.3
    diversity_score = min(len({s.get("source", "") for s in sources}) / 3.0, 1.0) * 0.2
    return round(source_score + length_score + diversity_score, 2)


def generate_session_id() -> str:
    import uuid

    return str(uuid.uuid4())
