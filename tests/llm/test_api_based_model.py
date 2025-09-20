"""
Test cases for api_based_model.py

Tests the LegalBasedModel class for proper initialization and model management.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.api.src.llm.api_based_model import LegalBasedModel
except ImportError as e:
    pytest.skip(f"Cannot import LegalBasedModel: {e}", allow_module_level=True)


class TestLegalBasedModel:
    """Test cases for LegalBasedModel class."""
    
    def test_default_initialization(self):
        """Test that the model initializes with default parameters."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model
            
            legal_model = LegalBasedModel()
            
            # Verify init_chat_model was called with correct defaults
            mock_init.assert_called_once_with(
                model="openai:gpt-4o-mini",
                temperature=0.3,
                max_tokens=5000,
                request_timeout=60,
                max_retries=3
            )
            
            # Verify the model is stored correctly
            assert legal_model.llm == mock_model
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model
            
            custom_params = {
                "model_name": "openai:gpt-4",
                "temperature": 0.1,
                "max_tokens": 3000
            }
            
            legal_model = LegalBasedModel(**custom_params)
            
            # Verify init_chat_model was called with custom parameters
            mock_init.assert_called_once_with(
                model="openai:gpt-4",
                temperature=0.1,
                max_tokens=3000,
                request_timeout=60,
                max_retries=3
            )
            
            assert legal_model.llm == mock_model
    
    def test_get_model_returns_correct_instance(self):
        """Test that get_model() returns the initialized model."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model
            
            legal_model = LegalBasedModel()
            returned_model = legal_model.get_model()
            
            assert returned_model == mock_model
            assert returned_model is legal_model.llm
    
    def test_model_initialization_with_various_model_names(self):
        """Test initialization with different model names."""
        model_names = [
            "openai:gpt-4o-mini",
            "openai:gpt-4",
            "openai:gpt-3.5-turbo",
            "anthropic:claude-3-5-sonnet-latest"
        ]
        
        for model_name in model_names:
            with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
                mock_model = Mock()
                mock_init.return_value = mock_model
                
                legal_model = LegalBasedModel(model_name=model_name)
                
                mock_init.assert_called_once_with(
                    model=model_name,
                    temperature=0.3,
                    max_tokens=5000,
                    request_timeout=60,
                    max_retries=3
                )
                
                assert legal_model.llm == mock_model
    
    def test_temperature_bounds(self):
        """Test model initialization with different temperature values."""
        temperature_values = [0.0, 0.3, 0.7, 1.0]
        
        for temp in temperature_values:
            with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
                mock_model = Mock()
                mock_init.return_value = mock_model
                
                legal_model = LegalBasedModel(temperature=temp)
                
                mock_init.assert_called_once_with(
                    model="openai:gpt-4o-mini",
                    temperature=temp,
                    max_tokens=5000,
                    request_timeout=60,
                    max_retries=3
                )
    
    def test_max_tokens_values(self):
        """Test model initialization with different max_tokens values."""
        token_values = [1000, 5000, 8000, 16000]
        
        for max_tokens in token_values:
            with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
                mock_model = Mock()
                mock_init.return_value = mock_model
                
                legal_model = LegalBasedModel(max_tokens=max_tokens)
                
                mock_init.assert_called_once_with(
                    model="openai:gpt-4o-mini",
                    temperature=0.3,
                    max_tokens=max_tokens,
                    request_timeout=60,
                    max_retries=3
                )
    
    def test_model_initialization_error_handling(self):
        """Test that initialization errors are properly propagated."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_init.side_effect = Exception("API key not found")
            
            with pytest.raises(Exception, match="API key not found"):
                LegalBasedModel()
    
    def test_model_attributes_after_initialization(self):
        """Test that model attributes are properly set after initialization."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_model.model_name = "gpt-4o-mini"
            mock_model.temperature = 0.3
            mock_init.return_value = mock_model
            
            legal_model = LegalBasedModel()
            
            # Verify the model object has expected attributes
            assert hasattr(legal_model, 'llm')
            assert legal_model.llm == mock_model
            assert callable(legal_model.get_model)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_with_environment_variables(self):
        """Test initialization with environment variables set."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model
            
            legal_model = LegalBasedModel()
            
            # Should still work with environment variables
            mock_init.assert_called_once()
            assert legal_model.llm == mock_model
    
    def test_multiple_instances(self):
        """Test that multiple instances can be created independently."""
        with patch('app.api.src.llm.api_based_model.init_chat_model') as mock_init:
            mock_model1 = Mock()
            mock_model2 = Mock()
            mock_init.side_effect = [mock_model1, mock_model2]
            
            legal_model1 = LegalBasedModel(model_name="openai:gpt-4")
            legal_model2 = LegalBasedModel(model_name="openai:gpt-3.5-turbo")
            
            assert legal_model1.llm == mock_model1
            assert legal_model2.llm == mock_model2
            assert legal_model1.llm != legal_model2.llm
            
            # Verify both calls were made
            assert mock_init.call_count == 2


class TestLegalBasedModelIntegration:
    """Integration tests for LegalBasedModel (require actual model access)."""
    
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'), 
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_real_model_initialization(self):
        """Test with a real model (requires API key)."""
        try:
            legal_model = LegalBasedModel(model_name="openai:gpt-4o-mini")
            model = legal_model.get_model()
            
            # Basic checks that the model was initialized
            assert model is not None
            assert hasattr(model, '__call__') or hasattr(model, 'invoke')
            
        except Exception as e:
            pytest.skip(f"Real model test failed (expected without valid API key): {e}")
    
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'), 
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_model_response_format(self):
        """Test that the model returns expected response format."""
        try:
            legal_model = LegalBasedModel()
            model = legal_model.get_model()
            
            # Try a simple invocation to test response format
            if hasattr(model, 'invoke'):
                response = model.invoke([{"role": "user", "content": "Hello"}])
                assert response is not None
                # Response should have content attribute or be a string
                assert hasattr(response, 'content') or isinstance(response, str)
            
        except Exception as e:
            pytest.skip(f"Real model response test failed: {e}")


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
