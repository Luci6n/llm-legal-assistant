"""
SQL Database Handler for Conversation Sessions

This module handles PostgreSQL storage for conversation sessions
using LangGraph's PostgresSaver for checkpointing.

Simple implementation for FYP project.
"""

import logging
from typing import Optional
from contextlib import contextmanager
from langgraph.checkpoint.postgres import PostgresSaver
from app.api.src.storage.db_config import db_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationSessionHandler:
    """
    Simple handler for conversation sessions using PostgreSQL.
    
    Manages conversation persistence using LangGraph's PostgresSaver.
    """
    
    def __init__(self):
        """Initialize the conversation session handler."""
        self._checkpointer = None
        logger.info("Conversation session handler initialized")
    
    def get_checkpointer(self) -> PostgresSaver:
        """
        Get PostgreSQL checkpointer for conversation persistence.
        
        Returns:
            PostgresSaver instance for LangGraph
        """
        if self._checkpointer is None:
            try:
                # Use the connection string from db_config
                connection_string = db_config.postgres.connection_string
                self._checkpointer = PostgresSaver.from_conn_string(connection_string)
                logger.info("PostgreSQL checkpointer created successfully")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL checkpointer: {e}")
                raise
        
        return self._checkpointer
    
    @contextmanager
    def get_checkpointer_context(self):
        """
        Context manager for PostgreSQL checkpointer.
        
        Yields:
            PostgresSaver instance
        """
        checkpointer = None
        try:
            connection_string = db_config.postgres.connection_string
            with PostgresSaver.from_conn_string(connection_string) as checkpointer:
                logger.info("PostgreSQL checkpointer context created")
                yield checkpointer
        except Exception as e:
            logger.error(f"PostgreSQL checkpointer context failed: {e}")
            raise
        finally:
            if checkpointer:
                logger.info("PostgreSQL checkpointer context closed")
    
    def create_session(self, thread_id: str) -> dict:
        """
        Create a new conversation session.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            
        Returns:
            Configuration dictionary for the session
        """
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        logger.info(f"Created session config for thread: {thread_id}")
        return config
    
    def test_connection(self) -> bool:
        """
        Test the PostgreSQL connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_checkpointer_context() as checkpointer:
                logger.info("PostgreSQL connection test successful")
                return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False


# Global instance for simple usage
conversation_handler = ConversationSessionHandler()


def get_conversation_handler() -> ConversationSessionHandler:
    """
    Get the global conversation session handler.
    
    Returns:
        ConversationSessionHandler instance
    """
    return conversation_handler


def create_session_config(thread_id: str) -> dict:
    """
    Simple function to create session configuration.
    
    Args:
        thread_id: Unique identifier for the conversation
        
    Returns:
        Configuration dictionary
    """
    return conversation_handler.create_session(thread_id)


# Example usage for FYP:
"""
# Test connection
handler = get_conversation_handler()
if handler.test_connection():
    print("Database connection successful!")

# Create session for conversation
session_config = create_session_config("user_123_conversation_1")

# Use with LangGraph
from langgraph.graph import StateGraph

with handler.get_checkpointer_context() as checkpointer:
    workflow = StateGraph(ChatState)
    # ... add nodes ...
    graph = workflow.compile(checkpointer=checkpointer)
    
    # Run conversation
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Hello"}]},
        config=session_config
    )
"""
