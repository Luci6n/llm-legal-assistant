"""
Memory Manager for the legal assistant.
Coordinates between short-term and long-term memory systems.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
from .short_term_memory import ShortTermMemory, SessionContext
from .long_term_memory import LongTermMemory, UserProfile, UserInteraction


class MemoryManager:
    """
    Manages both short-term and long-term memory for the legal assistant.
    Provides a unified interface for memory operations.
    """
    
    def __init__(
        self,
        storage_path: str = "memory_storage",
        embedding_model_path: str = "BAAI/bge-m3",
        short_term_window_size: int = 10,
        user_id: Optional[str] = None
    ):
        """
        Initialize memory manager.
        
        Args:
            storage_path: Path for persistent storage
            embedding_model_path: Path or name of BGE-M3 model
            short_term_window_size: Size of short-term memory window
            user_id: User ID for personalization
        """
        self.user_id = user_id or str(uuid.uuid4())
        
        # Initialize memory components
        self.long_term_memory = LongTermMemory(
            storage_path=storage_path,
            embedding_model_path=embedding_model_path
        )
        
        self.short_term_memory = ShortTermMemory(
            window_size=short_term_window_size,
            embedding_model_path=embedding_model_path,
            storage_path=f"{storage_path}/temp"
        )
        
        # Load or create user profile
        self.user_profile = self._initialize_user_profile()
        
    def _initialize_user_profile(self) -> UserProfile:
        """Initialize or load user profile."""
        profile = self.long_term_memory.get_user_profile(self.user_id)
        if not profile:
            profile = self.long_term_memory.create_or_update_user_profile(
                user_id=self.user_id,
                preferences={},
                expertise_level="beginner",
                legal_domains=[]
            )
        return profile
    
    def add_conversation_turn(
        self,
        user_input: str,
        ai_response: str,
        legal_domain: Optional[str] = None,
        case_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        topics: Optional[List[str]] = None,
        satisfaction_score: Optional[float] = None,
        store_long_term: bool = True
    ) -> str:
        """
        Add a conversation turn to both short-term and optionally long-term memory.
        
        Args:
            user_input: User's input message
            ai_response: AI's response
            legal_domain: Legal domain (e.g., "contract law", "criminal law")
            case_type: Type of case or query
            jurisdiction: Legal jurisdiction
            topics: List of topics discussed
            satisfaction_score: User satisfaction score (0.0 to 1.0)
            store_long_term: Whether to store in long-term memory
            
        Returns:
            Turn ID for tracking
        """
        # Prepare metadata
        metadata = {}
        if legal_domain:
            metadata['legal_domain'] = legal_domain
        if case_type:
            metadata['case_type'] = case_type
        if jurisdiction:
            metadata['jurisdiction'] = jurisdiction
        if topics:
            metadata['topics'] = topics
        if satisfaction_score is not None:
            metadata['satisfaction_score'] = satisfaction_score
        
        # Add to short-term memory
        turn_id = self.short_term_memory.add_message(
            user_input=user_input,
            ai_response=ai_response,
            metadata=metadata
        )
        
        # Update short-term context
        context_updates = {}
        if legal_domain:
            context_updates['legal_domain'] = legal_domain
        if case_type:
            context_updates['case_type'] = case_type
        if jurisdiction:
            context_updates['jurisdiction'] = jurisdiction
        if topics:
            context_updates['current_topics'] = topics
        
        if context_updates:
            self.short_term_memory.update_context(context_updates)
        
        # Store in long-term memory if requested
        if store_long_term:
            self.long_term_memory.store_interaction(
                user_id=self.user_id,
                user_input=user_input,
                ai_response=ai_response,
                legal_domain=legal_domain,
                case_type=case_type,
                jurisdiction=jurisdiction,
                satisfaction_score=satisfaction_score,
                topics=topics
            )
        
        return turn_id
    
    def search_memory(
        self,
        query: str,
        search_short_term: bool = True,
        search_long_term: bool = True,
        k_short: int = 3,
        k_long: int = 5,
        legal_domain: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search both short-term and long-term memory.
        
        Args:
            query: Search query
            search_short_term: Whether to search short-term memory
            search_long_term: Whether to search long-term memory
            k_short: Number of results from short-term memory
            k_long: Number of results from long-term memory
            legal_domain: Filter by legal domain
            
        Returns:
            Dictionary with 'short_term' and 'long_term' results
        """
        results = {
            'short_term': [],
            'long_term': []
        }
        
        if search_short_term:
            results['short_term'] = self.short_term_memory.search_conversation_semantic(
                query=query,
                k=k_short
            )
        
        if search_long_term:
            results['long_term'] = self.long_term_memory.search_similar_interactions(
                query=query,
                user_id=self.user_id,
                k=k_long,
                legal_domain=legal_domain
            )
        
        return results
    
    def search_legal_knowledge(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search legal knowledge base."""
        return self.long_term_memory.search_legal_concepts(query=query, k=k)
    
    def store_legal_concept(
        self,
        concept_name: str,
        definition: str,
        legal_domain: str,
        examples: Optional[List[str]] = None,
        related_concepts: Optional[List[str]] = None
    ) -> None:
        """Store a legal concept in long-term memory."""
        self.long_term_memory.store_legal_concept(
            concept_name=concept_name,
            definition=definition,
            legal_domain=legal_domain,
            examples=examples,
            related_concepts=related_concepts
        )
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        self.user_profile = self.long_term_memory.create_or_update_user_profile(
            user_id=self.user_id,
            preferences=preferences
        )
        
        # Update short-term context
        self.short_term_memory.update_context({
            'user_preferences': preferences
        })
    
    def update_user_expertise(self, expertise_level: str, legal_domains: List[str]) -> None:
        """Update user expertise level and domains."""
        self.user_profile = self.long_term_memory.create_or_update_user_profile(
            user_id=self.user_id,
            expertise_level=expertise_level,
            legal_domains=legal_domains
        )
    
    def get_session_context(self) -> Dict[str, Any]:
        """Get current session context."""
        short_term_context = self.short_term_memory.get_context_dict()
        
        # Enhance with user profile information
        enhanced_context = short_term_context.copy()
        enhanced_context['user_profile'] = {
            'user_id': self.user_profile.user_id,
            'expertise_level': self.user_profile.expertise_level,
            'legal_domains': self.user_profile.legal_domains,
            'preferences': self.user_profile.preferences,
            'interaction_count': self.user_profile.interaction_count
        }
        
        return enhanced_context
    
    def get_conversation_history(self, num_turns: Optional[int] = None) -> str:
        """Get formatted conversation history."""
        return self.short_term_memory.get_conversation_text(num_turns)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory summary."""
        short_term_stats = self.short_term_memory.get_memory_stats()
        long_term_analytics = self.long_term_memory.get_memory_analytics(self.user_id)
        
        return {
            'session': short_term_stats,
            'user_profile': {
                'user_id': self.user_profile.user_id,
                'expertise_level': self.user_profile.expertise_level,
                'legal_domains': self.user_profile.legal_domains,
                'creation_date': self.user_profile.creation_date.isoformat(),
                'last_active': self.user_profile.last_active.isoformat(),
                'total_interactions': self.user_profile.interaction_count
            },
            'long_term_analytics': long_term_analytics
        }
    
    def get_contextual_information(self, query: str) -> Dict[str, Any]:
        """
        Get contextual information for answering a query.
        Combines recent conversation, relevant past interactions, and legal knowledge.
        """
        # Get recent conversation
        recent_conversation = self.short_term_memory.get_conversation_text(5)
        
        # Search for relevant past interactions
        memory_search = self.search_memory(
            query=query,
            search_short_term=True,
            search_long_term=True,
            k_short=2,
            k_long=3
        )
        
        # Search legal knowledge
        legal_knowledge = self.search_legal_knowledge(query, k=3)
        
        # Get current context
        session_context = self.get_session_context()
        
        return {
            'recent_conversation': recent_conversation,
            'relevant_interactions': memory_search,
            'legal_knowledge': legal_knowledge,
            'session_context': session_context,
            'user_profile': {
                'expertise_level': self.user_profile.expertise_level,
                'legal_domains': self.user_profile.legal_domains,
                'preferences': self.user_profile.preferences
            }
        }
    
    def store_temporary_data(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """Store temporary data in short-term memory."""
        self.short_term_memory.store_temp_data(key, value, ttl_minutes)
    
    def get_temporary_data(self, key: str) -> Any:
        """Get temporary data from short-term memory."""
        return self.short_term_memory.get_temp_data(key)
    
    def clear_session(self) -> None:
        """Clear current session and start fresh."""
        self.short_term_memory.clear_memory()
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> None:
        """Clean up old long-term data."""
        self.long_term_memory.cleanup_old_data(days_to_keep)
    
    def get_user_interaction_history(
        self, 
        limit: int = 20,
        legal_domain: Optional[str] = None
    ) -> List[UserInteraction]:
        """Get user's interaction history from long-term memory."""
        return self.long_term_memory.get_user_interaction_history(
            user_id=self.user_id,
            limit=limit,
            legal_domain=legal_domain
        )
