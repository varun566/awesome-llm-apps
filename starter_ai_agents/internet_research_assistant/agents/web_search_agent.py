import concurrent.futures
import json
import time
from datetime import datetime
from typing import Optional
from duckduckgo_search import DDGS
from utils.cache import TTLCache
from utils.database import Database
from utils.helpers import make_cache_key, sanitize_query, truncate_text
from utils.logger import get_logger

logger = get_logger(__name__)


def search_web(
    query: str,
    max_results: int = 5,
    cache: Optional[TTLCache] = None,
    db: Optional[Database] = None,
    ttl: int = 3600,
) -> str:
    """
    Search the web using DuckDuckGo and return formatted results.
    Caches results in both memory (TTLCache) and SQLite (Database).
    """
    query = sanitize_query(query)
    if not query:
        return "No valid query provided."

    cache_key = make_cache_key(f"search:{query}:{max_results}")

    # 1. Check in-memory cache
    if cache:
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Memory cache hit for: {query[:60]}")
            return cached

    # 2. Check persistent cache
    if db:
        cached = db.cache_get(cache_key)
        if cached:
            logger.info(f"DB cache hit for: {query[:60]}")
            if cache:
                cache.set(cache_key, cached, ttl=ttl)
            return cached

    # 3. Live search
    start = time.perf_counter()
    results = _duckduckgo_search(query, max_results)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    if not results:
        return f"No search results found for: {query}"

    formatted = _format_results(query, results)

    # Store in caches
    if cache:
        cache.set(cache_key, formatted, ttl=ttl)
    if db:
        db.cache_set(cache_key, formatted, ttl_seconds=ttl)

    logger.info(f"Search completed in {elapsed_ms} ms for: {query[:60]}")
    return formatted


def _duckduckgo_search(query: str, max_results: int) -> list:
    """Execute a DuckDuckGo search with retry logic."""
    for attempt in range(3):
        try:
            date_aware_query = f"{query} {datetime.now().strftime('%Y')}"
            with DDGS() as ddgs:
                return list(ddgs.text(date_aware_query, max_results=max_results))
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
    return []


def _format_results(query: str, results: list) -> str:
    lines = [f"## Search Results for: {query}\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("href", r.get("url", ""))
        body = truncate_text(r.get("body", r.get("snippet", "")), 400)
        lines.append(f"### Result {i}: {title}\n**URL:** {url}\n{body}\n")
    return "\n".join(lines)


def multi_search(
    queries: list,
    max_results: int = 5,
    cache: Optional[TTLCache] = None,
    db: Optional[Database] = None,
    max_workers: int = 3,
) -> dict:
    """
    Run multiple searches concurrently and return a dict of {query: results}.
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(search_web, q, max_results, cache, db): q for q in queries
        }
        for future in concurrent.futures.as_completed(future_map):
            query = future_map[future]
            try:
                results[query] = future.result()
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                results[query] = f"Search error: {e}"
    return results
