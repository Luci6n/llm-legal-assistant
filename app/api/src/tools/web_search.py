"""
Core Web Search functionality - Framework agnostic
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

class WebSearchCore:
    """
    Core web search functionality using Google Serper API.
    Framework-agnostic implementation.
    """
    
    def __init__(self, api_key: Optional[str] = None, k: int = 10):
        """
        Initialize web search with API key.
        
        Args:
            api_key: Serper API key (optional, can use .env)
            k: Number of results to return
        """
        load_dotenv()
        api_key = api_key or os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("SERPER_API_KEY is required")
        
        self._search = GoogleSerperAPIWrapper(serper_api_key=api_key, k=k)
        self.k = k
    
    def search(self, query: str) -> str:
        """
        Execute search and return formatted results.
        
        Args:
            query: Search query string
            
        Returns:
            Search results as formatted string
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            logger.info(f"Executing search query: {query}")
            return self._search.run(query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def asearch(self, query: str) -> str:
        """
        Execute async search and return formatted results.
        
        Args:
            query: Search query string
            
        Returns:
            Search results as formatted string
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            logger.info(f"Executing async search query: {query}")
            return await self._search.arun(query)
        except Exception as e:
            logger.error(f"Async search failed: {e}")
            raise
    
    def get_structured_results(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get structured search results.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with search results or None if search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            return self._search.results(query)
        except Exception as e:
            logger.error(f"Failed to get structured results: {e}")
            return None
    
    async def aget_structured_results(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get structured search results asynchronously.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with search results or None if search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            return await self._search.aresults(query)
        except Exception as e:
            logger.error(f"Failed to get structured results: {e}")
            return None

# Alias for backward compatibility
WebSearch = WebSearchCore

# def main():
#     """Demo function"""
#     search = WebSearchCore()
    
#     # Test sync search
#     try:
#         query = "Latest AI research news"
#         result = search.search(query)
#         print("Search result:", result[:500], "...")
#     except Exception as e:
#         print("Search failed:", e)

# if __name__ == "__main__":
#     main()