"""
Conversation Memory Management for ZUS Chatbot
Tracks multi-turn conversations with context window
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Conversation:
    """Conversation session with memory"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_accessed = datetime.now()
    
    def get_recent_messages(self, n: int = 3) -> List[Message]:
        """Get last N message pairs (user + assistant)"""
        # Get last N*2 messages (N user + N assistant)
        return self.messages[-(n * 2):] if len(self.messages) >= n * 2 else self.messages
    
    def format_for_llm(self, n: int = 3) -> str:
        """Format recent conversation for LLM context"""
        recent = self.get_recent_messages(n)
        if not recent:
            return "No previous conversation."
        
        formatted = []
        for msg in recent:
            prefix = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{prefix}: {msg.content}")
        
        return "\n".join(formatted)
    
    def get_context_metadata(self) -> Dict:
        """Extract useful context from conversation history"""
        if not self.messages:
            return {}
        
        # Analyze conversation for context clues
        user_messages = [m.content.lower() for m in self.messages if m.role == "user"]
        
        context = {
            "total_messages": len(self.messages),
            "mentioned_products": any(
                keyword in " ".join(user_messages) 
                for keyword in ["tumbler", "cup", "bottle", "drinkware"]
            ),
            "mentioned_outlets": any(
                keyword in " ".join(user_messages)
                for keyword in ["outlet", "location", "store", "where"]
            ),
            "mentioned_cities": [],
        }
        
        # Extract mentioned cities
        cities = ["shah alam", "petaling jaya", "subang", "klang", "kuala lumpur"]
        for city in cities:
            if any(city in msg for msg in user_messages):
                context["mentioned_cities"].append(city)
        
        return context


class ConversationMemoryManager:
    """
    Manages multiple conversation sessions with automatic cleanup
    """
    
    def __init__(self, max_sessions: int = 1000, session_timeout_minutes: int = 30):
        """
        Args:
            max_sessions: Maximum number of sessions to keep in memory
            session_timeout_minutes: Minutes of inactivity before session expires
        """
        self.conversations: Dict[str, Conversation] = {}
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        logger.info(f"✅ ConversationMemoryManager initialized (max_sessions={max_sessions}, timeout={session_timeout_minutes}min)")
    
    def get_or_create_session(self, session_id: str) -> Conversation:
        """Get existing conversation or create new one"""
        # Cleanup old sessions first
        self._cleanup_expired_sessions()
        
        if session_id not in self.conversations:
            logger.info(f"📝 Creating new conversation session: {session_id}")
            self.conversations[session_id] = Conversation(session_id=session_id)
        else:
            logger.info(f"♻️  Retrieving existing conversation session: {session_id}")
        
        return self.conversations[session_id]
    
    def add_user_message(self, session_id: str, content: str, metadata: Dict = None):
        """Add user message to conversation"""
        conversation = self.get_or_create_session(session_id)
        conversation.add_message("user", content, metadata)
        logger.info(f"💬 User message added to session {session_id}")
    
    def add_assistant_message(self, session_id: str, content: str, metadata: Dict = None):
        """Add assistant response to conversation"""
        conversation = self.get_or_create_session(session_id)
        conversation.add_message("assistant", content, metadata)
        logger.info(f"🤖 Assistant message added to session {session_id}")
    
    def get_conversation_context(self, session_id: str, n: int = 3) -> str:
        """Get formatted conversation history for LLM"""
        if session_id not in self.conversations:
            return "No previous conversation."
        
        conversation = self.conversations[session_id]
        return conversation.format_for_llm(n)
    
    def get_context_metadata(self, session_id: str) -> Dict:
        """Get conversation context metadata"""
        if session_id not in self.conversations:
            return {}
        
        return self.conversations[session_id].get_context_metadata()
    
    def clear_session(self, session_id: str):
        """Clear a specific conversation session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"🗑️  Cleared conversation session: {session_id}")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to free memory"""
        now = datetime.now()
        expired = [
            sid for sid, conv in self.conversations.items()
            if now - conv.last_accessed > self.session_timeout
        ]
        
        for sid in expired:
            del self.conversations[sid]
        
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired sessions")
        
        # If still too many sessions, remove oldest
        if len(self.conversations) > self.max_sessions:
            sorted_sessions = sorted(
                self.conversations.items(),
                key=lambda x: x[1].last_accessed
            )
            to_remove = len(self.conversations) - self.max_sessions
            for sid, _ in sorted_sessions[:to_remove]:
                del self.conversations[sid]
            logger.info(f"🧹 Removed {to_remove} oldest sessions to stay under limit")
    
    def get_stats(self) -> Dict:
        """Get memory manager statistics"""
        return {
            "total_sessions": len(self.conversations),
            "max_sessions": self.max_sessions,
            "session_timeout_minutes": self.session_timeout.total_seconds() / 60,
            "oldest_session_age_minutes": (
                (datetime.now() - min(
                    (c.created_at for c in self.conversations.values()),
                    default=datetime.now()
                )).total_seconds() / 60
                if self.conversations else 0
            )
        }


# Global memory manager instance
memory_manager = ConversationMemoryManager(
    max_sessions=1000,
    session_timeout_minutes=30
)


def get_memory_manager() -> ConversationMemoryManager:
    """Get global memory manager instance"""
    return memory_manager
