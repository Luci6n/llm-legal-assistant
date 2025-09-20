"""
Short-term Memory Implementation for Legal Assistant

This module implements short-term memory using LangGraph's SummarizationNode for:
1. Document summarization (for RAG retrieval)
2. Chat conversation summarization (for conversation context)

Enhanced with LangMem tools for long-term memory management.
Simple implementation for FYP project.
"""

import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import langmem components, but handle gracefully if not available
try:
    # Patch for Python < 3.11 so langmem won't break
    import typing
    if not hasattr(typing, "NotRequired"):
        try:
            from typing_extensions import NotRequired
            typing.NotRequired = NotRequired
        except ImportError:
            raise ImportError(
                "typing_extensions is required for NotRequired in Python < 3.11. "
                "Run: pip install typing_extensions"
            )
    from langchain_core.messages.utils import count_tokens_approximately
    from langmem.short_term import SummarizationNode, RunningSummary
    LANGMEM_AVAILABLE = True
    logger.info("langmem successfully imported")
except ImportError as e:
    logger.warning(f"langmem not available - {e}")
    logger.warning("install with: pip install langmem")
    LANGMEM_AVAILABLE = False
    
    # Create placeholder classes for when langmem is not available
    class SummarizationNode:
        def __init__(self, **kwargs):
            self.config = kwargs
            logger.warning("Using placeholder SummarizationNode - install langmem for full functionality")
        
        def __call__(self, state):
            logger.warning("Placeholder SummarizationNode called - no actual summarization performed")
            return state
    
    class RunningSummary:
        pass
    
    def count_tokens_approximately(text):
        """Fallback token counter."""
        return len(str(text).split()) * 1.3  # Rough approximation

# Try to import LangMem memory tools for enhanced functionality
try:
    from langmem import create_manage_memory_tool, create_search_memory_tool
    from langgraph.store.postgres import PostgresStore
    from langgraph.store.memory import InMemoryStore
    LANGMEM_TOOLS_AVAILABLE = True
    logger.info("LangMem memory tools successfully imported")
except ImportError as e:
    logger.warning(f"LangMem memory tools not available - {e}")
    LANGMEM_TOOLS_AVAILABLE = False

class MemoryManager:
    """
    Simple memory manager for legal assistant conversations.
    
    Manages two types of summarization:
    1. Document summarization for RAG retrieval
    2. Chat conversation summarization for maintaining context
    """
    
    def __init__(self, summarizer_model):
        """
        Initialize memory manager with summarization nodes.
        
        Args:
            summarizer_model: The language model to use for summarization
        """
        self.summarizer_model = summarizer_model
        
        # Document summarizer for RAG retrieval
        self.doc_summarizer = SummarizationNode(
            token_counter=count_tokens_approximately,
            model=summarizer_model,
            max_tokens=4096,                # Each chunk up to ~4k tokens
            max_summary_tokens=512,         # Compressed summary of each chunk
            output_messages_key="doc_summaries",
            name="document_summarizer"
        )
        
        # Chat summarizer for conversation history
        self.chat_summarizer = SummarizationNode(
            token_counter=count_tokens_approximately,
            model=summarizer_model,
            max_tokens=1024,                # Shorter history window
            max_summary_tokens=256,         # Compact rolling summary
            output_messages_key="chat_summary",
            name="chat_summarizer"
        )
        
        # Initialize enhanced memory store if available
        self.store = None
        self.memory_tools = []
        self._initialize_enhanced_memory()
        
        logger.info("Memory manager initialized with document and chat summarizers")
    
    def _initialize_enhanced_memory(self):
        """Initialize enhanced memory capabilities with LangMem tools."""
        if not LANGMEM_TOOLS_AVAILABLE:
            logger.warning("Enhanced memory tools not available - using basic functionality only")
            return
        
        try:
            # Try PostgreSQL first, fallback to InMemoryStore
            db_uri = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
            
            try:
                self.store = PostgresStore.from_conn_string(db_uri)
                logger.info("Initialized PostgreSQL store for short-term memory")
            except Exception as e:
                logger.warning(f"PostgreSQL not available, using InMemoryStore: {e}")
                self.store = InMemoryStore(
                    index={
                        "dims": 1536,
                        "embed": "openai:text-embedding-3-small",
                    }
                )
                logger.info("Initialized InMemoryStore with semantic search")
            
            # Create memory management tools
            self.memory_tools = [
                create_manage_memory_tool(namespace=("legal_assistant", "user_memories")),
                create_search_memory_tool(namespace=("legal_assistant", "user_memories")),
            ]
            
            logger.info("Enhanced memory tools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced memory: {e}")
            self.store = None
            self.memory_tools = []
    
    def get_memory_tools(self):
        """Get the memory tools for use with agents."""
        return self.memory_tools if LANGMEM_TOOLS_AVAILABLE else []
    
    def get_store(self):
        """Get the memory store instance."""
        return self.store
    
    def summarize_documents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize documents for RAG retrieval.
        
        Args:
            state: Current graph state containing messages
            
        Returns:
            Updated state with document summaries
        """
        try:
            if LANGMEM_AVAILABLE:
                # Use real SummarizationNode invoke method
                result = self.doc_summarizer.invoke(state)
            else:
                # Use placeholder method
                result = self.doc_summarizer(state)
            logger.info("Document summarization completed")
            return result
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return state
    
    def summarize_chat(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize chat conversation for context management.
        
        Args:
            state: Current graph state containing messages
            
        Returns:
            Updated state with chat summary
        """
        try:
            if LANGMEM_AVAILABLE:
                # Use real SummarizationNode invoke method
                result = self.chat_summarizer.invoke(state)
            else:
                # Use placeholder method
                result = self.chat_summarizer(state)
            logger.info("Chat summarization completed")
            return result
        except Exception as e:
            logger.error(f"Chat summarization failed: {e}")
            return state
    
    def get_doc_summarizer(self) -> SummarizationNode:
        """Get the document summarization node."""
        return self.doc_summarizer
    
    def get_chat_summarizer(self) -> SummarizationNode:
        """Get the chat summarization node."""
        return self.chat_summarizer


def create_memory_manager(summarizer_model) -> MemoryManager:
    """
    Factory function to create a memory manager.
    
    Args:
        summarizer_model: The language model for summarization
        
    Returns:
        Configured MemoryManager instance
    """
    return MemoryManager(summarizer_model)


# Example usage for FYP:
"""
# Initialize with your model
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4.1")
memory_manager = create_memory_manager(model)

# Use in LangGraph
from langgraph.graph import StateGraph
from typing import TypedDict

class ChatState(TypedDict):
    messages: list
    doc_summaries: list
    chat_summary: list
    context: dict

# Create graph
workflow = StateGraph(ChatState)
workflow.add_node("summarize_docs", memory_manager.get_doc_summarizer())
workflow.add_node("summarize_chat", memory_manager.get_chat_summarizer())
"""
