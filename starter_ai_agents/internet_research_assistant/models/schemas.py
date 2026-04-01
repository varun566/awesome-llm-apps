from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = ""
    published_date: str = ""
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "published_date": self.published_date,
            "relevance_score": self.relevance_score,
        }


@dataclass
class ResearchQuery:
    query: str
    session_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    max_results: int = 5


@dataclass
class ResearchResponse:
    query: str
    answer: str
    sources: list = field(default_factory=list)
    confidence_score: float = 0.0
    related_questions: list = field(default_factory=list)
    processing_time: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "confidence_score": self.confidence_score,
            "related_questions": self.related_questions,
            "processing_time": self.processing_time,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConversationMessage:
    role: str
    content: str
    session_id: str
    message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


@dataclass
class CacheEntry:
    key: str
    value: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 3600
    hits: int = 0

    def is_expired(self) -> bool:
        age = (datetime.now(timezone.utc) - self.created_at.replace(tzinfo=timezone.utc) if self.created_at.tzinfo is None else self.created_at).total_seconds()
        return age > self.ttl_seconds


@dataclass
class AgentMessage:
    role: str
    content: str
    agent_name: str = ""
    tool_calls: list = field(default_factory=list)
