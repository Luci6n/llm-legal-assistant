"""
Combined Tools Manager for LLM Integration
Provides unified access to VectorSearch and WebSearch tools via LangChain interface.
"""

import logging
from typing import List, Dict, Any, Optional, Union
import asyncio
import gc
import threading

# LangChain imports
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Import torch for CUDA memory management if available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .vector_search import VectorSearch
from .web_search import WebSearchCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== Input Schemas ==========

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query string")

class VectorSearchInput(BaseModel):
    """Input schema for vector search tool"""
    query: str = Field(description="The search query for legal documents")
    collections: Union[str, List[str]] = Field(
        default="all",
        description="Collection(s) to search: 'legal_cases', 'legislation', 'all', or list of collections"
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of results to return (uses default if not specified)"
    )
    retriever_type: str = Field(
        default="hybrid",
        description="Type of retriever: 'hybrid', 'vector', or 'bm25'"
    )

class CombinedSearchInput(BaseModel):
    """Input schema for combined search (both vector and web)"""
    query: str = Field(description="The search query")
    include_vector_search: bool = Field(
        default=True,
        description="Whether to include vector search results"
    )
    include_web_search: bool = Field(
        default=True,
        description="Whether to include web search results"
    )
    collections: Union[str, List[str]] = Field(
        default="all",
        description="Collections for vector search"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of results per source"
    )

# ========== LangChain Tool Wrappers ==========
class WebSearchTool(BaseTool):
    """LangChain-compatible wrapper for WebSearch"""
    
    name: str = "web_search"
    description: str = (
        "A web search tool powered by the Google Serper API. "
        "Use this tool when you need up-to-date information from the internet "
        "that is not in your current knowledge. "
        "Provide a clear search query as input. "
        "Useful for answering questions about recent events, facts, news, or details "
        "that require an external source."
    )
    args_schema: type = WebSearchInput
    return_direct: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(self, web_search: WebSearchCore = None, **kwargs):
        super().__init__(**kwargs)
        self._web_search = web_search or WebSearchCore()
    
    @property
    def web_search(self):
        return self._web_search
    
    def _run(
        self, 
        query: str
    ) -> str:
        """Execute web search and return results"""
        try:
            logger.info(f"Web search: {query}")
            return self.web_search.search(query)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search failed: {str(e)}"
    
    async def _arun(
        self, 
        query: str
    ) -> str:
        """Async version of web search"""
        try:
            logger.info(f"Web search (async): {query}")
            return await self.web_search.asearch(query)
        except Exception as e:
            logger.error(f"Async web search failed: {e}")
            return f"Web search failed: {str(e)}"

class VectorSearchTool(BaseTool):
    """LangChain-compatible wrapper for VectorSearch"""
    
    name: str = "legal_vector_search"
    description: str = (
        "Search through legal documents including court cases and legislation. "
        "Use this tool to find relevant legal precedents, statutes, regulations, "
        "and case law. Supports hybrid search combining vector similarity and BM25 retrieval. "
        "Best for: legal research, finding similar cases, legislative analysis."
    )
    args_schema: type = VectorSearchInput
    return_direct: bool = False
    
    # Use model config for extra fields
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(self, vector_search: VectorSearch = None, **kwargs):
        super().__init__(**kwargs)
        self._vector_search = vector_search or VectorSearch()
    
    @property 
    def vector_search(self):
        return self._vector_search
    
    def _run(
        self,
        query: str,
        collections: Union[str, List[str]] = "all",
        top_k: Optional[int] = None,
        retriever_type: str = "hybrid",
    ) -> str:
        """Execute vector search and return formatted results"""
        try:
            logger.info(f"Legal vector search: {query}")
            
            # Use higher top_k for legal research if not specified
            search_top_k = top_k or 60  # Increased default
            
            # Perform the search
            results = self.vector_search.run_search(
                query=query,
                collections=collections,
                top_k=search_top_k,
                retriever_type=retriever_type
            )
            
            # Format results for LLM consumption
            formatted_results = self.vector_search.get_formatted_results(
                results=results,
                include_scores=True,
                max_content_length=1200,
                query_type="comprehensive"
            )
            
            return f"Legal Document Search Results:\n{formatted_results}"
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return f"Vector search failed: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        collections: Union[str, List[str]] = "all",
        top_k: Optional[int] = None,
        retriever_type: str = "hybrid",
    ) -> str:
        """Async version of vector search"""
        # Since VectorSearch is not async, run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._run,
            query,
            collections,
            top_k,
            retriever_type,
        )

class CombinedSearchTool(BaseTool):
    """LangChain-compatible tool that combines vector and web search"""
    
    name: str = "combined_search"
    description: str = (
        "Comprehensive search tool that combines legal document search with web search. "
        "Searches through local legal database (cases, legislation) AND current web information. "
        "Use when you need both legal precedents and current/updated information. "
        "Ideal for: recent legal developments, current law status, comprehensive research."
    )
    args_schema: type = CombinedSearchInput
    return_direct: bool = False
    
    # Use model config for extra fields
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(
        self, 
        vector_search: VectorSearch = None, 
        web_search: WebSearchCore = None,  # Use core class
        **kwargs
    ):
        super().__init__(**kwargs)
        self._vector_search = vector_search or VectorSearch()
        self._web_search = web_search or WebSearchCore()
    
    @property
    def vector_search(self):
        return self._vector_search
    
    @property 
    def web_search(self):
        return self._web_search
    
    def _run(
        self,
        query: str,
        include_vector_search: bool = True,
        include_web_search: bool = True,
        collections: Union[str, List[str]] = "all",
        top_k: Optional[int] = 5,
    ) -> str:
        """Execute combined search and return formatted results"""
        try:
            logger.info(f"Combined search: {query}")
            results_parts = []
            
            # Vector search
            if include_vector_search:
                try:
                    vector_results = self.vector_search.run_search(
                        query=query,
                        collections=collections,
                        top_k=top_k,
                        retriever_type="hybrid"
                    )
                    
                    formatted_vector = self.vector_search.get_formatted_results(
                        results=vector_results,
                        include_scores=True,
                        max_content_length=250
                    )
                    
                    results_parts.append(f"=== LEGAL DOCUMENTS SEARCH ===\n{formatted_vector}")
                    
                except Exception as e:
                    logger.error(f"Vector search component failed: {e}")
                    results_parts.append(f"=== LEGAL DOCUMENTS SEARCH ===\nSearch failed: {str(e)}")
            
            # Web search
            if include_web_search:
                try:
                    web_results = self._web_search.search(query)
                    results_parts.append(f"=== WEB SEARCH RESULTS ===\n{web_results}")
                    
                except Exception as e:
                    logger.error(f"Web search component failed: {e}")
                    results_parts.append(f"=== WEB SEARCH RESULTS ===\nSearch failed: {str(e)}")
            
            return "\n\n".join(results_parts)
            
        except Exception as e:
            logger.error(f"Combined search failed: {e}")
            return f"Combined search failed: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        include_vector_search: bool = True,
        include_web_search: bool = True,
        collections: Union[str, List[str]] = "all",
        top_k: Optional[int] = 5,
    ) -> str:
        """Async version of combined search"""
        try:
            logger.info(f"Combined search (async): {query}")
            results_parts = []
            
            # Create coroutines for concurrent execution
            tasks = []
            
            if include_vector_search:
                # Vector search in executor (since it's not async)
                loop = asyncio.get_event_loop()
                vector_task = loop.run_in_executor(
                    None,
                    lambda: self.vector_search.run_search(
                        query=query,
                        collections=collections,
                        top_k=top_k,
                        retriever_type="hybrid"
                    )
                )
                tasks.append(("vector", vector_task))
            
            if include_web_search:
                # Web search async
                web_task = self.web_search.asearch(query)
                tasks.append(("web", web_task))
            
            # Execute searches concurrently
            if tasks:
                completed_tasks = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )
                
                for i, (search_type, _) in enumerate(tasks):
                    result = completed_tasks[i]
                    
                    if isinstance(result, Exception):
                        logger.error(f"{search_type} search failed: {result}")
                        if search_type == "vector":
                            results_parts.append(f"=== LEGAL DOCUMENTS SEARCH ===\nSearch failed: {str(result)}")
                        else:
                            results_parts.append(f"=== WEB SEARCH RESULTS ===\nSearch failed: {str(result)}")
                    else:
                        if search_type == "vector":
                            formatted_vector = self.vector_search.get_formatted_results(
                                results=result,
                                include_scores=True,
                                max_content_length=250
                            )
                            results_parts.append(f"=== LEGAL DOCUMENTS SEARCH ===\n{formatted_vector}")
                        else:
                            results_parts.append(f"=== WEB SEARCH RESULTS ===\n{result}")
            
            return "\n\n".join(results_parts)
            
        except Exception as e:
            logger.error(f"Combined search (async) failed: {e}")
            return f"Combined search failed: {str(e)}"

# ========== Tools Manager ==========

class LegalToolsManager:
    """
    Manager class that provides access to all legal research tools.
    Creates LangChain-compatible tools for use with LLM agents.
    Uses shared instances to optimize memory usage, especially for GPU-based embeddings.
    """
    
    # Class-level shared instances to prevent memory duplication
    _shared_vector_search = None
    _shared_web_search = None
    _instance_lock = threading.Lock()
    _instance_count = 0
    
    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        vector_search_config: Optional[Dict[str, Any]] = None,
        force_new_instance: bool = False
    ):
        """
        Initialize the tools manager.
        
        Args:
            serper_api_key: API key for web search (optional, can use .env)
            vector_search_config: Configuration for vector search
            force_new_instance: If True, creates new instances instead of using shared ones
        """
        with self._instance_lock:
            self._instance_count += 1
        
        # Force garbage collection before initializing to free memory
        gc.collect()
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Initialize vector search (shared or new)
        if force_new_instance or self._shared_vector_search is None:
            vector_config = vector_search_config or {}
            if not force_new_instance:
                self._shared_vector_search = VectorSearch(**vector_config)
                self.vector_search = self._shared_vector_search
                logger.info("Created shared VectorSearch instance")
            else:
                self.vector_search = VectorSearch(**vector_config)
                logger.info("Created new VectorSearch instance")
        else:
            self.vector_search = self._shared_vector_search
            logger.info("Using existing shared VectorSearch instance")
        
        # Initialize web search (shared or new)
        try:
            if force_new_instance or self._shared_web_search is None:
                if serper_api_key:
                    web_search_core = WebSearchCore(api_key=serper_api_key)
                else:
                    web_search_core = WebSearchCore()
                
                if not force_new_instance:
                    self._shared_web_search = web_search_core
                    self.web_search_core = self._shared_web_search
                    logger.info("Created shared WebSearchCore instance")
                else:
                    self.web_search_core = web_search_core
                    logger.info("Created new WebSearchCore instance")
            else:
                self.web_search_core = self._shared_web_search
                logger.info("Using existing shared WebSearchCore instance")
                
        except Exception as e:
            logger.warning(f"Could not initialize web search: {e}")
            self.web_search_core = None
        
        # Create tool instances
        self.legal_vector_tool = VectorSearchTool(vector_search=self.vector_search)
        
        if self.web_search_core:
            self.web_search_tool = WebSearchTool(web_search=self.web_search_core)
            self.combined_tool = CombinedSearchTool(
                vector_search=self.vector_search,
                web_search=self.web_search_core  # Pass core, not wrapper
            )
        else:
            self.web_search_tool = None
            self.combined_tool = None
    
    def __del__(self):
        """Destructor to track instance cleanup"""
        with self._instance_lock:
            self._instance_count -= 1
            if self._instance_count <= 0:
                logger.info("Last LegalToolsManager instance being destroyed")
    
    @classmethod
    def cleanup_shared_resources(cls):
        """
        Clean up shared resources and free GPU memory.
        Call this when you're done with all tools to free memory.
        """
        with cls._instance_lock:
            if cls._shared_vector_search is not None:
                logger.info("Cleaning up shared VectorSearch instance")
                # Clean up the vector search instance
                if hasattr(cls._shared_vector_search, 'cleanup'):
                    cls._shared_vector_search.cleanup()
                cls._shared_vector_search = None
            
            if cls._shared_web_search is not None:
                logger.info("Cleaning up shared WebSearch instance")
                cls._shared_web_search = None
            
            # Force garbage collection
            gc.collect()
            
            # Clear CUDA cache if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("Cleared CUDA cache")
            
            cls._instance_count = 0
    
    @classmethod
    def get_memory_info(cls) -> Dict[str, Any]:
        """Get current memory usage information"""
        info = {
            "instance_count": cls._instance_count,
            "shared_vector_search_active": cls._shared_vector_search is not None,
            "shared_web_search_active": cls._shared_web_search is not None,
        }
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            info.update({
                "cuda_available": True,
                "cuda_memory_allocated": torch.cuda.memory_allocated(),
                "cuda_memory_reserved": torch.cuda.memory_reserved(),
                "cuda_memory_cached": torch.cuda.memory_cached() if hasattr(torch.cuda, 'memory_cached') else "N/A"
            })
        else:
            info["cuda_available"] = False
        
        return info
    
    def get_tools(self, include_web_search: bool = True) -> List[BaseTool]:
        """
        Get list of all available tools for LangChain agent.
        
        Args:
            include_web_search: Whether to include web search tools
            
        Returns:
            List of LangChain-compatible tools
        """
        tools = [self.legal_vector_tool]
        
        if include_web_search and self.web_search_tool:
            tools.append(self.web_search_tool)
        
        if include_web_search and self.combined_tool:
            tools.append(self.combined_tool)
        
        return tools
    
    def get_vector_only_tools(self) -> List[BaseTool]:
        """Get only vector search tools (no web search)"""
        return [self.legal_vector_tool]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        descriptions = {
            "legal_vector_search": self.legal_vector_tool.description,
        }
        
        if self.web_search_tool:
            descriptions["web_search"] = self.web_search_tool.description
        
        if self.combined_tool:
            descriptions["combined_search"] = self.combined_tool.description
        
        return descriptions
    
    def get_collection_stats(self) -> Dict[str, Dict]:
        """Get statistics about available document collections"""
        return self.vector_search.get_collection_stats()

# ========== Factory Functions ==========

def create_legal_tools(
    serper_api_key: Optional[str] = None,
    include_web_search: bool = True,
    vector_search_config: Optional[Dict[str, Any]] = None,
    force_new_instance: bool = False
) -> List[BaseTool]:
    """
    Factory function to create all legal research tools.
    
    Args:
        serper_api_key: API key for web search
        include_web_search: Whether to include web search capabilities
        vector_search_config: Configuration for vector search
        force_new_instance: If True, creates new instances instead of shared ones
        
    Returns:
        List of LangChain-compatible tools
    """
    manager = LegalToolsManager(
        serper_api_key=serper_api_key,
        vector_search_config=vector_search_config,
        force_new_instance=force_new_instance
    )
    
    return manager.get_tools(include_web_search=include_web_search)

def create_vector_search_tool(
    config: Optional[Dict[str, Any]] = None
) -> VectorSearchTool:
    """
    Factory function to create just the vector search tool.
    
    Args:
        config: Configuration for vector search
        
    Returns:
        LangChain-compatible vector search tool
    """
    vector_config = config or {}
    vector_search = VectorSearch(**vector_config)
    return VectorSearchTool(vector_search=vector_search)

# ========== Demo/Test Functions ==========

async def demo_tools():
    """Demo function showing how to use the tools with memory optimization"""
    print("=== Legal Tools Demo (Memory Optimized) ===\n")
    
    # Show initial memory state
    print("💾 Initial Memory State:")
    memory_info = LegalToolsManager.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Create tools manager (uses shared instances)
    print("🔧 Creating LegalToolsManager (using shared instances)...")
    manager = LegalToolsManager()
    
    # Show memory state after creation
    print("💾 Memory State After Creation:")
    memory_info = LegalToolsManager.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Get collection stats
    print("📊 Collection Statistics:")
    stats = manager.get_collection_stats()
    for collection, info in stats.items():
        print(f"  {collection}: {info}")
    print()
    
    # Test vector search
    print("🔍 Testing Vector Search:")
    query = "contract law breach of contract"
    vector_result = manager.legal_vector_tool._run(query=query, top_k=3)
    print(vector_result[:500] + "..." if len(vector_result) > 500 else vector_result)
    print()
    
    # Test web search (if available)
    if manager.web_search_tool:
        print("🌐 Testing Web Search:")
        web_result = await manager.web_search_tool._arun(query="recent contract law changes 2024")
        print(web_result[:500] + "..." if len(web_result) > 500 else web_result)
        print()
    
    # Test combined search (if available)
    if manager.combined_tool:
        print("🔄 Testing Combined Search:")
        combined_result = await manager.combined_tool._arun(
            query="artificial intelligence legal regulations",
            top_k=2
        )
        print(combined_result[:800] + "..." if len(combined_result) > 800 else combined_result)
        print()
    
    # Create another manager to show shared instance usage
    print("🔧 Creating Second LegalToolsManager (should use shared instances)...")
    manager2 = LegalToolsManager()
    
    # Show memory state with multiple managers
    print("💾 Memory State With Multiple Managers:")
    memory_info = LegalToolsManager.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Clean up
    print("🧹 Cleaning up shared resources...")
    LegalToolsManager.cleanup_shared_resources()
    
    # Show final memory state
    print("💾 Final Memory State After Cleanup:")
    memory_info = LegalToolsManager.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    print()

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_tools())