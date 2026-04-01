"""
Data models and schemas for Internet Research Assistant
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SearchSourceType(str, Enum):
    WEB = "web"
    ACADEMIC = "academic"
    NEWS = "news"
    SOCIAL = "social"

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: SearchSourceType
    date: Optional[datetime] = None
    reliability_score: float = 0.8
    
    class Config:
        use_enum_values = True

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = None
    sources: List[SearchResult] = []
    confidence_score: float = 0.0
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class Conversation(BaseModel):
    session_id: str
    messages: List[Message] = []
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        if data.get('updated_at') is None:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)

class ResearchQuery(BaseModel):
    query: str
    max_results: int = 10
    verify_facts: bool = True
    include_sources: bool = True
    confidence_threshold: float = 0.7

class ResearchResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: List[SearchResult]
    related_queries: List[str] = []
    verification_status: str  # 'verified', 'partial', 'unverified'
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class CacheEntry(BaseModel):
    key: str
    value: Any
    created_at: datetime = None
    expires_at: datetime = None
    hit_count: int = 0
    
    def __init__(self, **data):
        if data.get('created_at') is None:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)
