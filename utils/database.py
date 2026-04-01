"""
Database management for Internet Research Assistant
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.schemas import Message, Conversation
from config.settings import settings
from utils.logger import logger
import json

class Database:
    """SQLite database manager for persistence"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///, "")
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Conversations table
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
        ''')
        
        # Messages table
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT DEFAULT '[]',
                confidence_score REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id),
                INDEX idx_session_id (session_id),
                INDEX idx_timestamp (timestamp)
            )
        ''')
        
        # Analytics table
        c.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response_time REAL NOT NULL,
                confidence_score REAL,
                source_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id),
                INDEX idx_timestamp (timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def create_conversation(self, session_id: str, metadata: Dict = None) -> bool:
        """Create a new conversation"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                'INSERT INTO conversations (session_id, metadata) VALUES (?, ?)',
                (session_id, json.dumps(metadata or {}))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return False
    
    def save_message(self, session_id: str, message: Message) -> bool:
        """Save a message to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO messages (session_id, role, content, sources, confidence_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                message.role,
                message.content,
                json.dumps([s.dict() for s in message.sources]),
                message.confidence_score,
                message.timestamp
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """Retrieve conversation history"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('SELECT created_at, updated_at, metadata FROM conversations WHERE session_id = ?', 
                     (session_id,))
            conv_row = c.fetchone()
            
            if not conv_row:
                return None
            
            c.execute('''
                SELECT role, content, sources, confidence_score, timestamp 
                FROM messages WHERE session_id = ? ORDER BY timestamp
            ''', (session_id,))
            
            messages = []
            for row in c.fetchall():
                msg = Message(
                    role=row[0],
                    content=row[1],
                    sources=json.loads(row[2]),
                    confidence_score=row[3],
                    timestamp=datetime.fromisoformat(row[4])
                )
                messages.append(msg)
            
            conn.close()
            
            return Conversation(
                session_id=session_id,
                messages=messages,
                created_at=datetime.fromisoformat(conv_row[0]),
                updated_at=datetime.fromisoformat(conv_row[1]),
                metadata=json.loads(conv_row[2])
            )
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            return None
    
    def log_analytics(self, session_id: str, query: str, response_time: float, 
                     confidence_score: float = 0.0, source_count: int = 0) -> bool:
        """Log analytics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO analytics (session_id, query, response_time, confidence_score, source_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, query, response_time, confidence_score, source_count))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging analytics: {e}")
            return False
    
    def get_analytics(self, session_id: str = None, days: int = 7) -> List[Dict]:
        """Get analytics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if session_id:
                c.execute('''
                    SELECT query, response_time, confidence_score, source_count, timestamp 
                    FROM analytics 
                    WHERE session_id = ? AND timestamp > datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                ''', (session_id, days))
            else:
                c.execute('''
                    SELECT query, response_time, confidence_score, source_count, timestamp 
                    FROM analytics 
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                ''', (days,))
            
            results = []
            for row in c.fetchall():
                results.append({
                    'query': row[0],
                    'response_time': row[1],
                    'confidence_score': row[2],
                    'source_count': row[3],
                    'timestamp': row[4]
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error retrieving analytics: {e}")
            return []

# Global database instance
db = Database()
