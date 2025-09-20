"""
Test cases for memory.py

Tests the MemoryManager class for both original functionality and enhanced LangMem tools.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, call
import sys

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.api.src.memory.memory import MemoryManager, create_memory_manager
except ImportError as e:
    pytest.skip(f"Cannot import MemoryManager: {e}", allow_module_level=True)


class TestMemoryManagerBasic:
    """Test cases for basic MemoryManager functionality."""
    
    def test_initialization_without_langmem(self):
        """Test MemoryManager initialization when LangMem is not available."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', False):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                with patch('app.api.src.memory.memory.count_tokens_approximately') as mock_count:
                    mock_summ_instance = Mock()
                    mock_summ_node.return_value = mock_summ_instance
                    
                    memory_manager = MemoryManager(mock_model)
                    
                    # Verify initialization
                    assert memory_manager.summarizer_model == mock_model
                    assert memory_manager.doc_summarizer == mock_summ_instance
                    assert memory_manager.chat_summarizer == mock_summ_instance
                    
                    # Verify SummarizationNode was called twice (doc and chat)
                    assert mock_summ_node.call_count == 2
    
    def test_initialization_with_langmem_available(self):
        """Test MemoryManager initialization when LangMem is available."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                with patch('app.api.src.memory.memory.count_tokens_approximately') as mock_count:
                    mock_summ_instance = Mock()
                    mock_summ_node.return_value = mock_summ_instance
                    
                    memory_manager = MemoryManager(mock_model)
                    
                    # Verify basic initialization
                    assert memory_manager.summarizer_model == mock_model
                    assert memory_manager.doc_summarizer == mock_summ_instance
                    assert memory_manager.chat_summarizer == mock_summ_instance
    
    def test_doc_summarizer_configuration(self):
        """Test that document summarizer is configured correctly."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                with patch('app.api.src.memory.memory.count_tokens_approximately') as mock_count:
                    mock_summ_instance = Mock()
                    mock_summ_node.return_value = mock_summ_instance
                    
                    memory_manager = MemoryManager(mock_model)
                    
                    # Check that SummarizationNode was called with correct parameters for doc summarizer
                    doc_call = mock_summ_node.call_args_list[0]
                    args, kwargs = doc_call
                    
                    assert kwargs['model'] == mock_model
                    assert kwargs['max_tokens'] == 4096
                    assert kwargs['max_summary_tokens'] == 512
                    assert kwargs['output_messages_key'] == "doc_summaries"
                    assert kwargs['name'] == "document_summarizer"
    
    def test_chat_summarizer_configuration(self):
        """Test that chat summarizer is configured correctly."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                with patch('app.api.src.memory.memory.count_tokens_approximately') as mock_count:
                    mock_summ_instance = Mock()
                    mock_summ_node.return_value = mock_summ_instance
                    
                    memory_manager = MemoryManager(mock_model)
                    
                    # Check that SummarizationNode was called with correct parameters for chat summarizer
                    chat_call = mock_summ_node.call_args_list[1]
                    args, kwargs = chat_call
                    
                    assert kwargs['model'] == mock_model
                    assert kwargs['max_tokens'] == 1024
                    assert kwargs['max_summary_tokens'] == 256
                    assert kwargs['output_messages_key'] == "chat_summary"
                    assert kwargs['name'] == "chat_summarizer"
    
    def test_summarize_documents_success(self):
        """Test successful document summarization."""
        mock_model = Mock()
        test_state = {"messages": ["test message"]}
        expected_result = {"doc_summaries": ["summary"]}
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                mock_doc_summarizer = Mock()
                mock_chat_summarizer = Mock()
                mock_doc_summarizer.invoke.return_value = expected_result
                mock_summ_node.side_effect = [mock_doc_summarizer, mock_chat_summarizer]
                
                memory_manager = MemoryManager(mock_model)
                result = memory_manager.summarize_documents(test_state)
                
                mock_doc_summarizer.invoke.assert_called_once_with(test_state)
                assert result == expected_result
    
    def test_summarize_documents_error_handling(self):
        """Test error handling in document summarization."""
        mock_model = Mock()
        test_state = {"messages": ["test message"]}
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                mock_doc_summarizer = Mock()
                mock_chat_summarizer = Mock()
                mock_doc_summarizer.invoke.side_effect = Exception("Summarization failed")
                mock_summ_node.side_effect = [mock_doc_summarizer, mock_chat_summarizer]
                
                memory_manager = MemoryManager(mock_model)
                result = memory_manager.summarize_documents(test_state)
                
                # Should return original state on error
                assert result == test_state
    
    def test_summarize_chat_success(self):
        """Test successful chat summarization."""
        mock_model = Mock()
        test_state = {"messages": ["chat message"]}
        expected_result = {"chat_summary": ["summary"]}
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                mock_doc_summarizer = Mock()
                mock_chat_summarizer = Mock()
                mock_chat_summarizer.invoke.return_value = expected_result
                mock_summ_node.side_effect = [mock_doc_summarizer, mock_chat_summarizer]
                
                memory_manager = MemoryManager(mock_model)
                result = memory_manager.summarize_chat(test_state)
                
                mock_chat_summarizer.invoke.assert_called_once_with(test_state)
                assert result == expected_result
    
    def test_get_summarizers(self):
        """Test getting summarizer instances."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', True):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                mock_doc_summarizer = Mock()
                mock_chat_summarizer = Mock()
                mock_summ_node.side_effect = [mock_doc_summarizer, mock_chat_summarizer]
                
                memory_manager = MemoryManager(mock_model)
                
                assert memory_manager.get_doc_summarizer() == mock_doc_summarizer
                assert memory_manager.get_chat_summarizer() == mock_chat_summarizer


class TestMemoryManagerEnhanced:
    """Test cases for enhanced MemoryManager functionality with LangMem tools."""
    
    def test_enhanced_memory_initialization_postgres_success(self):
        """Test enhanced memory initialization with PostgreSQL success."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', True):
            with patch('app.api.src.memory.memory.PostgresStore') as mock_postgres:
                with patch('app.api.src.memory.memory.create_manage_memory_tool') as mock_manage:
                    with patch('app.api.src.memory.memory.create_search_memory_tool') as mock_search:
                        with patch('app.api.src.memory.memory.SummarizationNode'):
                            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
                                mock_store = Mock()
                                mock_postgres.from_conn_string.return_value = mock_store
                                mock_manage_tool = Mock()
                                mock_search_tool = Mock()
                                mock_manage.return_value = mock_manage_tool
                                mock_search.return_value = mock_search_tool
                                
                                memory_manager = MemoryManager(mock_model)
                                
                                # Verify PostgreSQL store was created
                                mock_postgres.from_conn_string.assert_called_once()
                                assert memory_manager.store == mock_store
                                
                                # Verify memory tools were created
                                assert len(memory_manager.memory_tools) == 2
                                assert mock_manage_tool in memory_manager.memory_tools
                                assert mock_search_tool in memory_manager.memory_tools
    
    def test_enhanced_memory_initialization_postgres_fallback(self):
        """Test enhanced memory initialization with PostgreSQL failure, falling back to InMemoryStore."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', True):
            with patch('app.api.src.memory.memory.PostgresStore') as mock_postgres:
                with patch('app.api.src.memory.memory.InMemoryStore') as mock_inmemory:
                    with patch('app.api.src.memory.memory.create_manage_memory_tool') as mock_manage:
                        with patch('app.api.src.memory.memory.create_search_memory_tool') as mock_search:
                            with patch('app.api.src.memory.memory.SummarizationNode'):
                                mock_postgres.from_conn_string.side_effect = Exception("DB connection failed")
                                mock_store = Mock()
                                mock_inmemory.return_value = mock_store
                                
                                memory_manager = MemoryManager(mock_model)
                                
                                # Verify fallback to InMemoryStore
                                mock_inmemory.assert_called_once_with(
                                    index={
                                        "dims": 1536,
                                        "embed": "openai:text-embedding-3-small",
                                    }
                                )
                                assert memory_manager.store == mock_store
    
    def test_enhanced_memory_tools_not_available(self):
        """Test enhanced memory when LangMem tools are not available."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', False):
            with patch('app.api.src.memory.memory.SummarizationNode'):
                memory_manager = MemoryManager(mock_model)
                
                # Verify no enhanced memory features
                assert memory_manager.store is None
                assert memory_manager.memory_tools == []
                assert memory_manager.get_memory_tools() == []
                assert memory_manager.get_store() is None
    
    def test_get_memory_tools_with_tools_available(self):
        """Test getting memory tools when available."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', True):
            with patch('app.api.src.memory.memory.InMemoryStore'):
                with patch('app.api.src.memory.memory.create_manage_memory_tool') as mock_manage:
                    with patch('app.api.src.memory.memory.create_search_memory_tool') as mock_search:
                        with patch('app.api.src.memory.memory.SummarizationNode'):
                            mock_manage_tool = Mock()
                            mock_search_tool = Mock()
                            mock_manage.return_value = mock_manage_tool
                            mock_search.return_value = mock_search_tool
                            
                            memory_manager = MemoryManager(mock_model)
                            tools = memory_manager.get_memory_tools()
                            
                            assert len(tools) == 2
                            assert mock_manage_tool in tools
                            assert mock_search_tool in tools
    
    def test_get_memory_tools_without_tools_available(self):
        """Test getting memory tools when not available."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', False):
            with patch('app.api.src.memory.memory.SummarizationNode'):
                memory_manager = MemoryManager(mock_model)
                tools = memory_manager.get_memory_tools()
                
                assert tools == []
    
    def test_memory_tool_namespace_configuration(self):
        """Test that memory tools are configured with correct namespace."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', True):
            with patch('app.api.src.memory.memory.InMemoryStore'):
                with patch('app.api.src.memory.memory.create_manage_memory_tool') as mock_manage:
                    with patch('app.api.src.memory.memory.create_search_memory_tool') as mock_search:
                        with patch('app.api.src.memory.memory.SummarizationNode'):
                            memory_manager = MemoryManager(mock_model)
                            
                            # Verify tools were created with correct namespace
                            expected_namespace = ("legal_assistant", "user_memories")
                            mock_manage.assert_called_once_with(namespace=expected_namespace)
                            mock_search.assert_called_once_with(namespace=expected_namespace)


class TestMemoryManagerFactory:
    """Test cases for the factory function."""
    
    def test_create_memory_manager_factory(self):
        """Test the factory function creates a MemoryManager correctly."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.SummarizationNode'):
            memory_manager = create_memory_manager(mock_model)
            
            assert isinstance(memory_manager, MemoryManager)
            assert memory_manager.summarizer_model == mock_model


class TestMemoryManagerErrorHandling:
    """Test cases for error handling in MemoryManager."""
    
    def test_initialization_with_invalid_model(self):
        """Test initialization with invalid model."""
        with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
            mock_summ_node.side_effect = Exception("Invalid model")
            
            with pytest.raises(Exception, match="Invalid model"):
                MemoryManager(None)
    
    def test_enhanced_memory_initialization_complete_failure(self):
        """Test enhanced memory initialization when everything fails."""
        mock_model = Mock()
        
        with patch('app.api.src.memory.memory.LANGMEM_TOOLS_AVAILABLE', True):
            with patch('app.api.src.memory.memory.PostgresStore') as mock_postgres:
                with patch('app.api.src.memory.memory.InMemoryStore') as mock_inmemory:
                    with patch('app.api.src.memory.memory.create_manage_memory_tool') as mock_manage:
                        with patch('app.api.src.memory.memory.SummarizationNode'):
                            # Make everything fail
                            mock_postgres.from_conn_string.side_effect = Exception("DB failed")
                            mock_inmemory.side_effect = Exception("Memory failed")
                            mock_manage.side_effect = Exception("Tools failed")
                            
                            memory_manager = MemoryManager(mock_model)
                            
                            # Should handle errors gracefully
                            assert memory_manager.store is None
                            assert memory_manager.memory_tools == []
    
    def test_summarization_without_langmem_available(self):
        """Test summarization when LangMem is not available."""
        mock_model = Mock()
        test_state = {"messages": ["test"]}
        
        with patch('app.api.src.memory.memory.LANGMEM_AVAILABLE', False):
            with patch('app.api.src.memory.memory.SummarizationNode') as mock_summ_node:
                mock_summarizer = Mock()
                mock_summarizer.return_value = test_state  # placeholder behavior
                mock_summ_node.return_value = mock_summarizer
                
                memory_manager = MemoryManager(mock_model)
                
                # Should still work with placeholder
                result = memory_manager.summarize_documents(test_state)
                assert result == test_state


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
