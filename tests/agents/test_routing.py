"""
Test cases for routing.py

Tests the multi-agent legal assistant routing system including:
- Individual agent creation and configuration
- Supervisor agent functionality  
- Multi-agent graph coordination
- Memory integration
- Error handling and fallbacks
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, call
import sys
from typing import Dict, Any

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.api.src.agents.routing import LegalAgentSystem, create_legal_agent_system, LegalAgentState
    from app.api.src.agents.routing import load_prompt_template
except ImportError as e:
    pytest.skip(f"Cannot import routing modules: {e}", allow_module_level=True)


class TestPromptLoading:
    """Test cases for prompt template loading functionality."""
    
    def test_load_prompt_template_success(self):
        """Test successful loading of prompt template."""
        mock_content = "Test prompt content"
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = "test_path.md"
                mock_open.return_value.__enter__.return_value.read.return_value = mock_content
                
                result = load_prompt_template("test_prompt.md")
                
                assert result == mock_content
                mock_open.assert_called_once_with("test_path.md", 'r', encoding='utf-8')
    
    def test_load_prompt_template_file_not_found(self):
        """Test handling of missing prompt template file."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = load_prompt_template("nonexistent.md")
            assert result == ""
    
    def test_load_prompt_template_other_error(self):
        """Test handling of other errors during prompt loading."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = load_prompt_template("restricted.md")
            assert result == ""


class TestLegalAgentState:
    """Test cases for LegalAgentState."""
    
    def test_legal_agent_state_default_values(self):
        """Test that LegalAgentState has proper default values."""
        state = LegalAgentState(
            user_id="default_user",
            session_id="default_session", 
            current_agent="supervisor",
            context={}
        )
        
        assert state.get("user_id") == "default_user"
        assert state.get("session_id") == "default_session"
        assert state.get("current_agent") == "supervisor"
        assert state.get("context") == {}
    
    def test_legal_agent_state_custom_values(self):
        """Test LegalAgentState with custom values."""
        custom_state = LegalAgentState(
            messages=[{"role": "user", "content": "test"}],
            user_id="test_user",
            session_id="test_session",
            current_agent="research_agent",
            context={"key": "value"}
        )
        
        assert custom_state["user_id"] == "test_user"
        assert custom_state["session_id"] == "test_session"
        assert custom_state["current_agent"] == "research_agent"
        assert custom_state["context"]["key"] == "value"


class TestLegalAgentSystemInitialization:
    """Test cases for LegalAgentSystem initialization."""
    
    def test_initialization_default_model(self):
        """Test initialization with default model."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver') as mock_saver:
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            system = LegalAgentSystem()
                            
                            # Verify initialization
                            mock_model_class.assert_called_once_with(model_name="openai:gpt-4o-mini")
                            assert system.model_name == "openai:gpt-4o-mini"
                            assert system.model_manager == mock_model_instance
    
    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        custom_model = "openai:gpt-4"
        
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver') as mock_saver:
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            system = LegalAgentSystem(model_name=custom_model)
                            
                            mock_model_class.assert_called_once_with(model_name=custom_model)
                            assert system.model_name == custom_model
    
    def test_agent_creation(self):
        """Test that all specialized agents are created."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver') as mock_saver:
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_base_model = Mock()
                            mock_model_instance.get_model.return_value = mock_base_model
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_agent = Mock()
                            mock_create_agent.return_value = mock_agent
                            
                            system = LegalAgentSystem()
                            
                            # Verify all agents were created
                            assert system.research_agent == mock_agent
                            assert system.summarization_agent == mock_agent
                            assert system.prediction_agent == mock_agent
                            assert system.supervisor_agent == mock_agent
                            
                            # Verify create_react_agent was called for each agent (3 workers + 1 supervisor)
                            assert mock_create_agent.call_count == 4


class TestLegalAgentSystemAgentCreation:
    """Test cases for individual agent creation methods."""
    
    def test_create_research_agent(self):
        """Test creation of research agent."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="research prompt"):
                            # Setup mocks
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_base_model = Mock()
                            mock_model_instance.get_model.return_value = mock_base_model
                            
                            mock_memory_instance = Mock()
                            mock_memory_tools = [Mock(), Mock()]
                            mock_memory_instance.get_memory_tools.return_value = mock_memory_tools
                            mock_memory_instance.get_store.return_value = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            
                            mock_agent = Mock()
                            mock_create_agent.return_value = mock_agent
                            
                            system = LegalAgentSystem()
                            
                            # Verify research agent creation call
                            research_call = None
                            for call_args in mock_create_agent.call_args_list:
                                args, kwargs = call_args
                                if kwargs.get('name') == 'legal_research_agent':
                                    research_call = kwargs
                                    break
                            
                            assert research_call is not None
                            assert research_call['model'] == mock_base_model
                            assert research_call['tools'] == mock_memory_tools
                            assert research_call['name'] == 'legal_research_agent'
    
    def test_create_handoff_tool(self):
        """Test creation of handoff tools for agent communication."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            with patch('langchain_core.tools.tool') as mock_tool:
                                mock_model_instance = Mock()
                                mock_model_class.return_value = mock_model_instance
                                mock_model_instance.get_model.return_value = Mock()
                                
                                mock_memory_instance = Mock()
                                mock_memory_class.return_value = mock_memory_instance
                                mock_memory_instance.get_memory_tools.return_value = []
                                mock_memory_instance.get_store.return_value = Mock()
                                
                                mock_create_agent.return_value = Mock()
                                
                                system = LegalAgentSystem()
                                
                                # Test handoff tool creation
                                handoff_tool = system._create_handoff_tool("test_agent", "Test description")
                                
                                # Verify tool decorator was called
                                mock_tool.assert_called()
                                call_args = mock_tool.call_args
                                assert call_args[0][0] == "transfer_to_test_agent"
                                assert call_args[1]['description'] == "Test description"


class TestLegalAgentSystemGraphBuilding:
    """Test cases for graph building functionality."""
    
    def test_build_graph_with_supervisor_available(self):
        """Test graph building when langgraph-supervisor is available."""
        with patch('app.api.src.agents.routing.SUPERVISOR_AVAILABLE', True):
            with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
                with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                    with patch('app.api.src.agents.routing.InMemorySaver'):
                        with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                            with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                                with patch('app.api.src.agents.routing.create_supervisor') as mock_create_supervisor:
                                    # Setup mocks
                                    mock_model_instance = Mock()
                                    mock_model_class.return_value = mock_model_instance
                                    mock_model_instance.get_model.return_value = Mock()
                                    
                                    mock_memory_instance = Mock()
                                    mock_memory_class.return_value = mock_memory_instance
                                    mock_memory_instance.get_memory_tools.return_value = []
                                    mock_memory_instance.get_store.return_value = Mock()
                                    
                                    mock_create_agent.return_value = Mock()
                                    
                                    mock_supervisor_graph = Mock()
                                    mock_supervisor_graph.compile.return_value = Mock()
                                    mock_create_supervisor.return_value = mock_supervisor_graph
                                    
                                    system = LegalAgentSystem()
                                    
                                    # Verify prebuilt supervisor was used
                                    mock_create_supervisor.assert_called_once()
    
    def test_build_graph_without_supervisor_available(self):
        """Test graph building when langgraph-supervisor is not available."""
        with patch('app.api.src.agents.routing.SUPERVISOR_AVAILABLE', False):
            with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
                with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                    with patch('app.api.src.agents.routing.InMemorySaver'):
                        with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                            with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                                with patch('app.api.src.agents.routing.StateGraph') as mock_state_graph:
                                    # Setup mocks
                                    mock_model_instance = Mock()
                                    mock_model_class.return_value = mock_model_instance
                                    mock_model_instance.get_model.return_value = Mock()
                                    
                                    mock_memory_instance = Mock()
                                    mock_memory_class.return_value = mock_memory_instance
                                    mock_memory_instance.get_memory_tools.return_value = []
                                    mock_memory_instance.get_store.return_value = Mock()
                                    
                                    mock_create_agent.return_value = Mock()
                                    
                                    mock_workflow = Mock()
                                    mock_state_graph.return_value = mock_workflow
                                    mock_workflow.compile.return_value = Mock()
                                    
                                    system = LegalAgentSystem()
                                    
                                    # Verify custom graph was built
                                    mock_state_graph.assert_called_once()
                                    assert mock_workflow.add_node.call_count >= 4  # supervisor + 3 agents
                                    assert mock_workflow.add_edge.call_count >= 4  # edges between nodes


class TestLegalAgentSystemInvoke:
    """Test cases for the invoke functionality."""
    
    def test_invoke_success(self):
        """Test successful query processing."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            # Setup mocks
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            # Mock the graph
                            mock_graph = Mock()
                            expected_result = {"messages": [{"role": "assistant", "content": "Test response"}]}
                            mock_graph.invoke.return_value = expected_result
                            
                            system = LegalAgentSystem()
                            system.graph = mock_graph  # Override the graph
                            
                            result = system.invoke("Test query", "user123", "session456")
                            
                            # Verify invoke was called with correct parameters
                            mock_graph.invoke.assert_called_once()
                            call_args = mock_graph.invoke.call_args
                            input_state = call_args[0][0]  # First argument 
                            config = call_args[1]['config']  # Keyword argument
                            
                            assert input_state['messages'][0]['content'] == "Test query"
                            assert input_state['user_id'] == "user123"
                            assert input_state['session_id'] == "session456"
                            assert config['configurable']['thread_id'] == "user123_session456"
                            assert config['configurable']['user_id'] == "user123"
                            
                            assert result == expected_result
    
    def test_invoke_error_handling(self):
        """Test error handling in invoke."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            # Setup mocks
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            # Mock the graph to raise an error
                            mock_graph = Mock()
                            mock_graph.invoke.side_effect = Exception("Processing failed")
                            
                            system = LegalAgentSystem()
                            system.graph = mock_graph
                            
                            result = system.invoke("Test query")
                            
                            # Verify error handling
                            assert "error" in result
                            assert "Processing failed" in result["error"]
                            assert "I apologize" in result["messages"][0]["content"]
    
    def test_stream_functionality(self):
        """Test streaming functionality."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            # Setup mocks
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            # Mock the graph stream
                            mock_graph = Mock()
                            mock_stream_data = [
                                {"supervisor": {"messages": [{"role": "assistant", "content": "Chunk 1"}]}},
                                {"supervisor": {"messages": [{"role": "assistant", "content": "Chunk 2"}]}}
                            ]
                            mock_graph.stream.return_value = iter(mock_stream_data)
                            
                            system = LegalAgentSystem()
                            system.graph = mock_graph
                            
                            chunks = list(system.stream("Test query"))
                            
                            assert len(chunks) == 2
                            assert chunks[0] == mock_stream_data[0]
                            assert chunks[1] == mock_stream_data[1]
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                            # Setup mocks
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            # Mock the graph state
                            mock_graph = Mock()
                            mock_state = Mock()
                            mock_messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
                            mock_state.values = {"messages": mock_messages}
                            mock_graph.get_state.return_value = mock_state
                            
                            system = LegalAgentSystem()
                            system.graph = mock_graph
                            
                            history = system.get_conversation_history("user123", "session456")
                            
                            mock_graph.get_state.assert_called_once()
                            call_config = mock_graph.get_state.call_args[0][0]
                            assert call_config['configurable']['thread_id'] == "user123_session456"
                            
                            assert history == mock_messages


class TestLegalAgentSystemFactoryFunction:
    """Test cases for the factory function."""
    
    def test_create_legal_agent_system_default(self):
        """Test factory function with default parameters."""
        with patch('app.api.src.agents.routing.LegalAgentSystem') as mock_system_class:
            mock_system = Mock()
            mock_system_class.return_value = mock_system
            
            result = create_legal_agent_system()
            
            mock_system_class.assert_called_once_with(model_name="openai:gpt-4o-mini")
            assert result == mock_system
    
    def test_create_legal_agent_system_custom_model(self):
        """Test factory function with custom model."""
        custom_model = "openai:gpt-4"
        
        with patch('app.api.src.agents.routing.LegalAgentSystem') as mock_system_class:
            mock_system = Mock()
            mock_system_class.return_value = mock_system
            
            result = create_legal_agent_system(model_name=custom_model)
            
            mock_system_class.assert_called_once_with(model_name=custom_model)
            assert result == mock_system


class TestLegalAgentSystemErrorScenarios:
    """Test cases for various error scenarios."""
    
    def test_initialization_with_missing_prompts(self):
        """Test initialization when prompt templates are missing."""
        with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
            with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                with patch('app.api.src.agents.routing.InMemorySaver'):
                    with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                        with patch('app.api.src.agents.routing.load_prompt_template', return_value=""):  # Empty prompts
                            mock_model_instance = Mock()
                            mock_model_class.return_value = mock_model_instance
                            mock_model_instance.get_model.return_value = Mock()
                            
                            mock_memory_instance = Mock()
                            mock_memory_class.return_value = mock_memory_instance
                            mock_memory_instance.get_memory_tools.return_value = []
                            mock_memory_instance.get_store.return_value = Mock()
                            
                            mock_create_agent.return_value = Mock()
                            
                            # Should still initialize successfully with empty prompts
                            system = LegalAgentSystem()
                            assert system is not None
    
    def test_graph_compilation_error(self):
        """Test handling of graph compilation errors."""
        with patch('app.api.src.agents.routing.SUPERVISOR_AVAILABLE', False):
            with patch('app.api.src.agents.routing.LegalBasedModel') as mock_model_class:
                with patch('app.api.src.agents.routing.MemoryManager') as mock_memory_class:
                    with patch('app.api.src.agents.routing.InMemorySaver'):
                        with patch('app.api.src.agents.routing.create_react_agent') as mock_create_agent:
                            with patch('app.api.src.agents.routing.load_prompt_template', return_value="test prompt"):
                                with patch('app.api.src.agents.routing.StateGraph') as mock_state_graph:
                                    # Setup mocks
                                    mock_model_instance = Mock()
                                    mock_model_class.return_value = mock_model_instance
                                    mock_model_instance.get_model.return_value = Mock()
                                    
                                    mock_memory_instance = Mock()
                                    mock_memory_class.return_value = mock_memory_instance
                                    mock_memory_instance.get_memory_tools.return_value = []
                                    mock_memory_instance.get_store.return_value = Mock()
                                    
                                    mock_create_agent.return_value = Mock()
                                    
                                    mock_workflow = Mock()
                                    mock_state_graph.return_value = mock_workflow
                                    mock_workflow.compile.side_effect = Exception("Compilation failed")
                                    
                                    with pytest.raises(Exception, match="Compilation failed"):
                                        LegalAgentSystem()


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
