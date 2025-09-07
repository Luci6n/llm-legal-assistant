"""
Short-term memory module for the legal assistant.
Handles conversation context and immediate session memory.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass
from collections import deque
import chromadb
from FlagEmbedding import BGEM3FlagModel


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    timestamp: datetime
    user_input: str
    ai_response: str
    turn_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SessionContext:
    """Represents the current session context."""
    session_id: str
    start_time: datetime
    legal_domain: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    current_topics: List[str] = None
    user_preferences: Dict[str, Any] = None
    active_documents: List[str] = None
    
    def __post_init__(self):
        if self.current_topics is None:
            self.current_topics = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.active_documents is None:
            self.active_documents = []


class ShortTermMemory:
    """
    Manages short-term memory for legal conversations.
    Includes conversation history, context window, and session-based memory.
    """
    
    def __init__(
        self, 
        window_size: int = 10,
        max_turns_for_search: int = 50,
        embedding_model_path: str = "BAAI/bge-m3",
        storage_path: str = "temp_memory"
    ):
        """
        Initialize short-term memory.
        
        Args:
            window_size: Number of conversation turns to keep in working memory
            max_turns_for_search: Maximum turns to store for semantic search
            embedding_model_path: Path or name of BGE-M3 model
            storage_path: Path for temporary storage
        """
        self.window_size = window_size
        self.max_turns_for_search = max_turns_for_search
        self.storage_path = storage_path
        
        # Initialize BGE-M3 model for semantic search
        self.embedding_model = BGEM3FlagModel(embedding_model_path, use_fp16=True)
        
        # Initialize session
        self.session_context = SessionContext(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now()
        )
        
        # Conversation storage
        self.conversation_turns = deque(maxlen=window_size)
        self.all_turns = deque(maxlen=max_turns_for_search)  # For semantic search
        
        # Temporary storage for current session
        self.temp_storage = {}
        
        # Initialize in-memory vector store for semantic search of recent conversation
        self.chroma_client = chromadb.Client()
        self.conversation_collection = self.chroma_client.get_or_create_collection(
            name=f"session_{self.session_context.session_id}",
            metadata={"hnsw:space": "cosine"}
        )
        
    def add_message(self, user_input: str, ai_response: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a conversation turn to memory."""
        turn_id = str(uuid.uuid4())
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            ai_response=ai_response,
            turn_id=turn_id,
            metadata=metadata or {}
        )
        
        # Add to working memory
        self.conversation_turns.append(turn)
        self.all_turns.append(turn)
        
        # Add to vector store for semantic search
        conversation_text = f"User: {user_input}\nAssistant: {ai_response}"
        embedding = self.embedding_model.encode([conversation_text])['dense_vecs'][0].tolist()
        
        turn_metadata = {
            "timestamp": turn.timestamp.isoformat(),
            "turn_id": turn_id,
            "user_input": user_input,
            "ai_response": ai_response
        }
        if metadata:
            turn_metadata.update(metadata)
        
        self.conversation_collection.add(
            embeddings=[embedding],
            documents=[conversation_text],
            metadatas=[turn_metadata],
            ids=[turn_id]
        )
        
        return turn_id
    
    def get_recent_conversation(self, num_turns: Optional[int] = None) -> List[ConversationTurn]:
        """Get recent conversation history."""
        if num_turns is None:
            return list(self.conversation_turns)
        else:
            return list(self.conversation_turns)[-num_turns:]
    
    def get_conversation_text(self, num_turns: Optional[int] = None, include_metadata: bool = False) -> str:
        """Get conversation as formatted text."""
        turns = self.get_recent_conversation(num_turns)
        conversation_parts = []
        
        for turn in turns:
            conversation_parts.append(f"User: {turn.user_input}")
            conversation_parts.append(f"Assistant: {turn.ai_response}")
            
            if include_metadata and turn.metadata:
                conversation_parts.append(f"Metadata: {json.dumps(turn.metadata)}")
            conversation_parts.append("")  # Empty line for separation
        
        return "\n".join(conversation_parts)
    
    def search_conversation_semantic(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search conversation history semantically."""
        if self.conversation_collection.count() == 0:
            return []
        
        query_embedding = self.embedding_model.encode([query])['dense_vecs'][0].tolist()
        
        results = self.conversation_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.conversation_collection.count())
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def update_context(self, context_updates: Dict[str, Any]) -> None:
        """Update session context with new information."""
        for key, value in context_updates.items():
            if hasattr(self.session_context, key):
                if key == "current_topics" and isinstance(value, list):
                    # Merge topics, keep unique
                    current_topics = set(self.session_context.current_topics)
                    current_topics.update(value)
                    self.session_context.current_topics = list(current_topics)[-5:]  # Keep last 5 topics
                elif key == "user_preferences" and isinstance(value, dict):
                    self.session_context.user_preferences.update(value)
                elif key == "active_documents" and isinstance(value, list):
                    # Keep only recent documents
                    current_docs = set(self.session_context.active_documents)
                    current_docs.update(value)
                    self.session_context.active_documents = list(current_docs)[-10:]  # Keep last 10 docs
                else:
                    setattr(self.session_context, key, value)
    
    def get_context(self) -> SessionContext:
        """Get current session context."""
        return self.session_context
    
    def get_context_dict(self) -> Dict[str, Any]:
        """Get session context as dictionary."""
        return {
            "session_id": self.session_context.session_id,
            "start_time": self.session_context.start_time.isoformat(),
            "legal_domain": self.session_context.legal_domain,
            "case_type": self.session_context.case_type,
            "jurisdiction": self.session_context.jurisdiction,
            "current_topics": self.session_context.current_topics,
            "user_preferences": self.session_context.user_preferences,
            "active_documents": self.session_context.active_documents
        }
    
    def store_temp_data(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """Store temporary data for the current session."""
        expiry_time = datetime.now() + timedelta(minutes=ttl_minutes)
        self.temp_storage[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "expires_at": expiry_time
        }
    
    def get_temp_data(self, key: str) -> Any:
        """Retrieve temporary data."""
        if key in self.temp_storage:
            data = self.temp_storage[key]
            if datetime.now() < data["expires_at"]:
                return data["value"]
            else:
                # Remove expired data
                del self.temp_storage[key]
        return None
    
    def clear_expired_temp_data(self) -> None:
        """Clear expired temporary data."""
        current_time = datetime.now()
        expired_keys = [
            key for key, data in self.temp_storage.items()
            if current_time >= data["expires_at"]
        ]
        for key in expired_keys:
            del self.temp_storage[key]
    
    def get_memory_summary(self) -> str:
        """Generate a summary of the current conversation."""
        if not self.conversation_turns:
            return "No conversation history available."
        
        recent_turns = list(self.conversation_turns)
        topics = set()
        
        # Extract topics from context and metadata
        topics.update(self.session_context.current_topics)
        
        for turn in recent_turns:
            if turn.metadata and 'topics' in turn.metadata:
                topics.update(turn.metadata['topics'])
        
        summary_parts = []
        summary_parts.append(f"Session started: {self.session_context.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append(f"Conversation turns: {len(self.conversation_turns)}")
        
        if self.session_context.legal_domain:
            summary_parts.append(f"Legal domain: {self.session_context.legal_domain}")
        
        if self.session_context.case_type:
            summary_parts.append(f"Case type: {self.session_context.case_type}")
        
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(list(topics)[:5])}")
        
        return "\n".join(summary_parts)
    
    def get_memory_variables(self) -> Dict[str, Any]:
        """Get all memory variables for prompt formatting."""
        return {
            "conversation_history": self.get_conversation_text(),
            "recent_turns": [
                {"user": turn.user_input, "assistant": turn.ai_response}
                for turn in self.get_recent_conversation(5)
            ],
            "session_context": self.get_context_dict(),
            "conversation_summary": self.get_memory_summary(),
            "session_duration": str(datetime.now() - self.session_context.start_time),
            "temp_data_keys": list(self.temp_storage.keys())
        }
    
    def clear_memory(self) -> None:
        """Clear all short-term memory and start new session."""
        # Clear conversation data
        self.conversation_turns.clear()
        self.all_turns.clear()
        self.temp_storage.clear()
        
        # Delete old collection and create new one
        try:
            self.chroma_client.delete_collection(f"session_{self.session_context.session_id}")
        except:
            pass  # Collection might not exist
        
        # Create new session
        self.session_context = SessionContext(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now()
        )
        
        # Create new collection
        self.conversation_collection = self.chroma_client.get_or_create_collection(
            name=f"session_{self.session_context.session_id}",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        self.clear_expired_temp_data()  # Clean up first
        
        return {
            "session_id": self.session_context.session_id,
            "conversation_turns": len(self.conversation_turns),
            "total_turns_stored": len(self.all_turns),
            "session_duration": str(datetime.now() - self.session_context.start_time),
            "temp_storage_items": len(self.temp_storage),
            "active_topics": len(self.session_context.current_topics),
            "active_documents": len(self.session_context.active_documents),
            "vector_store_count": self.conversation_collection.count(),
            "legal_domain": self.session_context.legal_domain,
            "case_type": self.session_context.case_type,
            "jurisdiction": self.session_context.jurisdiction
        }
