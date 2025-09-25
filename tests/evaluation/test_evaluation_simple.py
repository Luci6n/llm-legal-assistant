#!/usr/bin/env python3
"""
Simple pytest test suite for the Legal AI Judge evaluation system.

This is a simplified version that focuses on the core functionality.

Run with: pytest test_evaluation_simple.py -v
"""

import pytest
import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the API source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'api', 'src'))

from evaluation.evaluation import LegalAIJudge
from langfuse import Evaluation


class TestLegalAIJudgeSimple:
    """Simplified test suite for the LegalAIJudge class"""

    @pytest.fixture
    def judge(self):
        """Create a LegalAIJudge instance for testing"""
        return LegalAIJudge(model="gpt-4o", temperature=0.1)

    @pytest.fixture
    def mock_json_response(self):
        """Mock OpenAI API response with valid JSON"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 4,
            "reasoning": "Good response with proper structure and content"
        })
        return mock_response

    @pytest.fixture
    def mock_text_response(self):
        """Mock OpenAI API response that requires regex fallback"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The score is 3 out of 5 for this response."
        return mock_response

    @pytest.mark.asyncio
    async def test_legal_research_evaluation(self, judge, mock_json_response):
        """Test legal research evaluation with JSON response"""
        async_mock = AsyncMock(return_value=mock_json_response)
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
            result = await judge.evaluate_legal_research(
                query="What are the elements of a valid contract?",
                answer="Disclaimer: This is legal research.\n\nFindings:\n1. Offer\n2. Acceptance\n3. Consideration"
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 4.0

    @pytest.mark.asyncio
    async def test_legal_research_regex_fallback(self, judge, mock_text_response):
        """Test legal research evaluation with regex fallback"""
        async_mock = AsyncMock(return_value=mock_text_response)
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
            result = await judge.evaluate_legal_research(
                query="What is a contract?",
                answer="A contract is an agreement"
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 3.0

    @pytest.mark.asyncio
    async def test_legal_summarization_evaluation(self, judge, mock_json_response):
        """Test legal summarization evaluation"""
        async_mock = AsyncMock(return_value=mock_json_response)
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
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

    @pytest.mark.asyncio
    async def test_legal_prediction_evaluation(self, judge, mock_json_response):
        """Test legal prediction evaluation"""
        async_mock = AsyncMock(return_value=mock_json_response)
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
            result = await judge.evaluate_legal_prediction(
                case_scenario="Contract breach case with damages",
                prediction={"outcome": "plaintiff wins", "damages": "$10000"},
                ground_truth={"outcome": "plaintiff wins", "damages": "$10000"}
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_prediction_quality"
            assert result.value == 4.0

    @pytest.mark.asyncio
    async def test_api_error_handling(self, judge):
        """Test handling of OpenAI API errors"""
        async_mock = AsyncMock(side_effect=Exception("API Error"))
        
        with patch.object(judge.client.chat.completions, 'create', async_mock):
            result = await judge.evaluate_legal_research(
                query="Test query",
                answer="Test response"
            )
            
            assert isinstance(result, Evaluation)
            assert result.name == "legal_research_quality"
            assert result.value == 0.0
            assert "Evaluation failed" in result.comment
            assert "API Error" in result.comment

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


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])