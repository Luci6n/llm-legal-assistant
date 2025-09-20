"""
Memory module for the legal assistant.
Provides short-term memory capabilities using LangGraph summarization.
"""

from .memory import MemoryManager, create_memory_manager

__all__ = [
    "MemoryManager",
    "create_memory_manager"
]