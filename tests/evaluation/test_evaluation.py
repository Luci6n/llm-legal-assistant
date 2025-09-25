#!/usr/bin/env python3
"""
Pytest test suite for the Legal AI Judge evaluation system.

This test suite covers:
- Legal research evaluation
- Legal summarization evaluation  
- Legal prediction evaluation
- Error handling and edge cases
- JSON parsing and response validation

Run with: pytest test_evaluation.py -v
"""

import pytest
import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the API source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.src.evaluation.evaluation import LegalAIJudge
from langfuse import Evaluation


class TestLegalAIJudge:
    """Test suite for the LegalAIJudge class"""

    @pytest.fixture
    def judge(self):
        """Create a LegalAIJudge instance for testing"""
        return LegalAIJudge(model="gpt-4o", temperature=0.1)

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 4,
            "reasoning": "Good response with proper structure and content"
        })
        return mock_response

    @pytest.fixture
    def mock_openai_response_fallback(self):
        """Mock OpenAI API response that requires regex fallback"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The score is 3 out of 5 for this response."
        return mock_response

    @pytest.mark.asyncio
    async def test_evaluate_legal_research_success(self, judge, mock_openai_response):
        """Test successful legal research evaluation"""
        print(f"Mock response content: {mock_openai_response.choices[0].message.content}")
        
        # Create an async mock for the API call
        async_mock = AsyncMock(return_value=mock_openai_response)
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
            result = await judge.evaluate_legal_research(
                query="What are the elements of a valid contract?",
                answer="Disclaimer: This is legal research.\n\nFindings:\n1. Offer\n2. Acceptance\n3. Consideration"
            )
            
            print(f"Result value: {result.value}")
            print(f"Result comment: {result.comment}")
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 4.0
            assert "Good response" in result.comment

    @pytest.mark.asyncio
    async def test_evaluate_legal_research_fallback_parsing(self, judge, mock_openai_response_fallback):
        """Test legal research evaluation with regex fallback parsing"""
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_openai_response_fallback):
            result = await judge.evaluate_legal_research(
                query="What is a contract?",
                answer="A contract is an agreement"
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 3.0
            assert "Raw response" in result.comment

    @pytest.mark.asyncio
    async def test_evaluate_legal_summarization_success(self, judge, mock_openai_response):
        """Test successful legal summarization evaluation"""
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_openai_response):
            result = await judge.evaluate_legal_summarization(
                document="This is a long legal document about contract disputes...",
                summary="**Summarized Document**: Contract dispute case.\n\n**Key Points**:\n- Breach of contract\n- Damages awarded",
                reference_summary={
                    "summarized_documents": "Contract dispute case", 
                    "key_points": ["breach", "damages"]
                }
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_summarization_quality"
            assert result.value == 4.0
            assert "Good response" in result.comment

    @pytest.mark.asyncio
    async def test_evaluate_legal_summarization_no_reference(self, judge, mock_openai_response):
        """Test legal summarization evaluation without reference summary"""
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_openai_response):
            result = await judge.evaluate_legal_summarization(
                document="Legal document text",
                summary="**Summarized Document**: Brief summary.\n\n**Key Points**:\n- Point 1",
                reference_summary=None
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_summarization_quality"
            assert result.value == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_legal_prediction_success(self, judge, mock_openai_response):
        """Test successful legal prediction evaluation"""
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_openai_response):
            result = await judge.evaluate_legal_prediction(
                case_scenario="Contract breach case with damages",
                prediction={"outcome": "plaintiff wins", "damages": "$10000"},
                ground_truth={"outcome": "plaintiff wins", "damages": "$10000"}
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_prediction_quality"
            assert result.value == 4.0
            assert "Good response" in result.comment

    @pytest.mark.asyncio
    async def test_evaluate_legal_prediction_no_ground_truth(self, judge, mock_openai_response):
        """Test legal prediction evaluation without ground truth"""
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_openai_response):
            result = await judge.evaluate_legal_prediction(
                case_scenario="Contract case",
                prediction={"outcome": "defendant wins"},
                ground_truth=None
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_prediction_quality"
            assert result.value == 4.0

    @pytest.mark.asyncio
    async def test_api_error_handling(self, judge):
        """Test handling of OpenAI API errors"""
        with patch.object(judge.client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = await judge.evaluate_legal_research(
                query="Test query",
                answer="Test response"
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 0.0
            assert "Evaluation failed" in result.comment
            assert "API Error" in result.comment

    @pytest.mark.asyncio
    async def test_invalid_json_fallback(self, judge):
        """Test fallback when OpenAI returns invalid JSON"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response with score 2"
        
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_response):
            result = await judge.evaluate_legal_research(
                query="Test query",
                answer="Test response"
            )
            
            assert isinstance(result, Evaluation)
            assert result.value == 2.0  # Should extract "2" using regex
            assert "Raw response" in result.comment

    @pytest.mark.asyncio
    async def test_no_score_in_response(self, judge):
        """Test fallback when no score can be extracted"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "No numeric score in this response"
        
        with patch.object(judge.client.chat.completions, 'create', return_value=mock_response):
            result = await judge.evaluate_legal_research(
                query="Test query",
                answer="Test response"
            )
            
            assert isinstance(result, Evaluation)
            assert result.value == 0.0  # Should default to 0.0
            assert "Raw response" in result.comment

    def test_judge_initialization(self):
        """Test LegalAIJudge initialization"""
        judge = LegalAIJudge(model="gpt-3.5-turbo", temperature=0.5)
        assert judge.model == "gpt-3.5-turbo"
        assert judge.temperature == 0.5
        assert judge.client is not None

    def test_judge_initialization_defaults(self):
        """Test LegalAIJudge initialization with defaults"""
        judge = LegalAIJudge()
        assert judge.model == "gpt-4o"
        assert judge.temperature == 0.1
        assert judge.client is not None

    @pytest.mark.asyncio
    async def test_string_replacement_in_prompts(self, judge, mock_openai_response):
        """Test that prompt templates correctly replace placeholders"""
        
        # Capture the actual prompt sent to OpenAI
        captured_prompt = None
        
        async def capture_prompt(*args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs['messages'][0]['content']
            return mock_openai_response
            
        with patch.object(judge.client.chat.completions, 'create', side_effect=capture_prompt):
            await judge.evaluate_legal_research(
                query="Test query input",
                answer="Test response output"
            )
            
            # Verify that placeholders were replaced
            assert captured_prompt is not None
            assert "Test query input" in captured_prompt
            assert "Test response output" in captured_prompt
            assert "{{input}}" not in captured_prompt
            assert "{{output}}" not in captured_prompt

    @pytest.mark.asyncio
    async def test_large_document_truncation(self, judge, mock_openai_response):
        """Test that large documents are properly truncated in summarization"""
        large_document = "A" * 2000  # Document larger than 1000 chars
        
        captured_prompt = None
        
        async def capture_prompt(*args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs['messages'][0]['content']
            return mock_openai_response
            
        with patch.object(judge.client.chat.completions, 'create', side_effect=capture_prompt):
            await judge.evaluate_legal_summarization(
                document=large_document,
                summary="Test summary"
            )
            
            # Verify truncation occurred
            assert "A" * 1000 + "..." in captured_prompt
            assert len([line for line in captured_prompt.split('\n') if 'A' * 1000 in line]) > 0

    @pytest.mark.asyncio 
    async def test_json_ground_truth_serialization(self, judge, mock_openai_response):
        """Test that ground truth objects are properly serialized to JSON"""
        captured_prompt = None
        
        async def capture_prompt(*args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs['messages'][0]['content']
            return mock_openai_response
            
        ground_truth = {"outcome": "plaintiff wins", "damages": 50000}
        
        with patch.object(judge.client.chat.completions, 'create', side_effect=capture_prompt):
            await judge.evaluate_legal_prediction(
                case_scenario="Test case",
                prediction={"outcome": "defendant wins"},
                ground_truth=ground_truth
            )
            
            # Verify JSON serialization
            assert '"outcome": "plaintiff wins"' in captured_prompt
            assert '"damages": 50000' in captured_prompt


class TestEvaluationClass:
    """Test the Evaluation data class"""
    
    def test_evaluation_creation(self):
        """Test creating an Evaluation instance"""
        eval_result = Evaluation(
            name="test_evaluation",
            value=3.5,
            comment="Test comment"
        )
        
        assert eval_result.name == "test_evaluation"
        assert eval_result.value == 3.5
        assert eval_result.comment == "Test comment"

    def test_evaluation_string_representation(self):
        """Test string representation of Evaluation"""
        eval_result = Evaluation(
            name="test_eval",
            value=4.0,
            comment="Good result"
        )
        
        str_repr = str(eval_result)
        assert "test_eval" in str_repr
        assert "4.0" in str_repr


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])