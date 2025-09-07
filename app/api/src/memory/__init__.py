"""
Memory module for the legal assistant.
Provides short-term and long-term memory capabilities with BGE-M3 embeddings and Chroma vector storage.
"""

from .short_term_memory import ShortTermMemory, ConversationTurn, SessionContext
from .long_term_memory import LongTermMemory, UserProfile, UserInteraction
from .memory_manager import MemoryManager

__all__ = [
    "ShortTermMemory",
    "LongTermMemory", 
    "MemoryManager",
    "ConversationTurn",
    "SessionContext",
    "UserProfile",
    "UserInteraction"
]