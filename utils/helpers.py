"""
Helper utilities for Internet Research Assistant
"""
import re
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import asyncio
from config.settings import settings
from utils.logger import logger

def sanitize_query(query: str) -> str:
    """Sanitize search query"""
    query = query.strip()
    query = re.sub(r'\s+', ' ', query)
    return query

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        domain = urlparse(url).netloc
        return domain.replace('www.', '')
    except:
        return "unknown"

def calculate_query_hash(query: str) -> str:
    """Calculate hash for query caching"""
    return hashlib.md5(query.encode()).hexdigest()

async def run_concurrent(tasks: List, max_concurrent: int = 3) -> List[Any]:
    """Run tasks concurrently with limit"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[bounded_task(task) for task in tasks])

def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def calculate_confidence_score(sources_count: int, avg_reliability: float) -> float:
    """Calculate confidence score for answer"""
    # Base score from number of sources (max 0.5)
    source_score = min(sources_count / 5 * 0.5, 0.5)
    # Reliability score (max 0.5)
    reliability_score = avg_reliability * 0.5
    return min(source_score + reliability_score, 1.0)

def rank_sources(sources: List[Dict]) -> List[Dict]:
    """Rank sources by reliability and recency"""
    def source_score(source):
        reliability = source.get('reliability_score', 0.8)
        recency = source.get('recency_score', 0.7)
        return reliability * 0.7 + recency * 0.3
    
    return sorted(sources, key=source_score, reverse=True)

def format_sources_for_display(sources: List[Dict]) -> str:
    """Format sources for display in UI"""
    if not sources:
        return "No sources found"
    
    formatted = "**Sources:**\n"
    for i, source in enumerate(sources[:5], 1):
        title = source.get('title', 'Unknown')
        url = source.get('url', '#')
        formatted += f"{i}. [{title}]({url})\n"
    
    return formatted
"""