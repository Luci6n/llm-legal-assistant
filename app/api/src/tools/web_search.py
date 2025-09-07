from typing import Optional, Dict, Any
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class WebSearch:
    def __init__(self, api_key: str):
        load_dotenv()
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.search = GoogleSerperAPIWrapper(serper_api_key=api_key or os.getenv("SERPER_API_KEY"))
        
    async def run_search(self, query: str, num_results: int = 10) -> str:
        """
        Execute a web search query asynchronously.
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
            
        Returns:
            Search results as string
            
        Raises:
            ValueError: If query is empty
            Exception: If search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        try:
            logger.info(f"Executing search query: {query}")
            # Use arun for async execution
            return await self.search.arun(query)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise
    
    async def get_search_results(self, query: str, num_results: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get structured search results asynchronously.
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
        
        Returns:
            Dictionary with search results or None if search fails
            
        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Use aresults for async execution
            return await self.search.aresults(query)
        except Exception as e:
            logger.error(f"Failed to get structured results: {str(e)}")
            return None