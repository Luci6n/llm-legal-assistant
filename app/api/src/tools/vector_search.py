"""
Vector Search Tool for Legal Cases and Legislation
Provides unified search capabilities across multiple document collections.
"""

import logging
from typing import List, Dict, Union
from dataclasses import dataclass

from ..storage.vdb_handler import HybridVDBRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Container for search results with metadata"""
    content: str
    score: float
    source_collection: str
    collection_type: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
# ========== Input Schemas ==========

class VectorSearch:
    """
    Unified vector search tool for legal documents.
    Supports searching across legal cases and legislation collections.
    """
    
    def __init__(
        self, 
        embed_model_name: str = "BAAI/bge-m3",
        rerank_model_name: str = "BAAI/bge-reranker-large",
        similarity_top_k: int = 300,
        top_n_rerank: int = 60,
        **kwargs
    ):
        """
        Initialize the vector search tool.
        
        Args:
            embed_model_name: Name of the embedding model
            rerank_model_name: Name of the reranking model  
            similarity_top_k: Number of documents to retrieve before reranking
            top_n_rerank: Number of documents to return after reranking
        """
        self.similarity_top_k = similarity_top_k
        self.top_n_rerank = top_n_rerank
        
        # Initialize single retriever (efficient approach)
        self.retriever = HybridVDBRetriever(
            embed_model_name=embed_model_name,
            rerank_model_name=rerank_model_name,
            collection_type="legal_cases",  # Start with legal cases
            similarity_top_k=similarity_top_k,
            top_n_rerank=top_n_rerank
        )
        
        self.current_collection_type = "legal_cases"
        logger.info("VectorSearch initialized with single retriever approach")
    
    def search_legal_cases(
        self, 
        query: str, 
        top_k: int = None,
        retriever_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Search in legal cases collection.
        
        Args:
            query: Search query string
            top_k: Number of results to return (uses default if None)
            retriever_type: Type of retriever ("hybrid", "vector", "bm25")
            
        Returns:
            List of SearchResult objects
        """
        return self._search_collection(
            query=query,
            collection_type="legal_cases", 
            top_k=top_k,
            retriever_type=retriever_type
        )
    
    def search_legislation(
        self, 
        query: str, 
        top_k: int = None,
        retriever_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Search in legislation collection.
        
        Args:
            query: Search query string
            top_k: Number of results to return (uses default if None)
            retriever_type: Type of retriever ("hybrid", "vector", "bm25")
            
        Returns:
            List of SearchResult objects
        """
        return self._search_collection(
            query=query,
            collection_type="legislation",
            top_k=top_k,
            retriever_type=retriever_type
        )
    
    def search_all_collections(
        self, 
        query: str, 
        top_k: int = None,
        retriever_type: str = "hybrid"
    ) -> Dict[str, List[SearchResult]]:
        """
        Search across all available collections.
        
        Args:
            query: Search query string
            top_k: Number of results to return per collection
            retriever_type: Type of retriever ("hybrid", "vector", "bm25")
            
        Returns:
            Dictionary mapping collection types to search results
        """
        results = {}
        
        # Search legal cases
        try:
            legal_results = self.search_legal_cases(query, top_k, retriever_type)
            results["legal_cases"] = legal_results
        except Exception as e:
            logger.error(f"Error searching legal cases: {e}")
            results["legal_cases"] = []
        
        # Search legislation
        try:
            legislation_results = self.search_legislation(query, top_k, retriever_type)
            results["legislation"] = legislation_results
        except Exception as e:
            logger.error(f"Error searching legislation: {e}")
            results["legislation"] = []
        
        return results
    
    def run_search(
        self, 
        query: str, 
        collections: Union[str, List[str]] = "all",
        top_k: int = None,
        retriever_type: str = "hybrid"
    ) -> Union[List[SearchResult], Dict[str, List[SearchResult]]]:
        """
        Main search interface - supports single or multiple collections.
        
        Args:
            query: Search query string
            collections: Collection(s) to search ("legal_cases", "legislation", "all", or list)
            top_k: Number of results to return
            retriever_type: Type of retriever ("hybrid", "vector", "bm25")
            
        Returns:
            Search results - List for single collection, Dict for multiple
        """
        if isinstance(collections, str):
            if collections == "all":
                return self.search_all_collections(query, top_k, retriever_type)
            elif collections == "legal_cases":
                return self.search_legal_cases(query, top_k, retriever_type)
            elif collections == "legislation":
                return self.search_legislation(query, top_k, retriever_type)
            else:
                raise ValueError(f"Unknown collection: {collections}")
        
        elif isinstance(collections, list):
            results = {}
            for collection in collections:
                if collection == "legal_cases":
                    results["legal_cases"] = self.search_legal_cases(query, top_k, retriever_type)
                elif collection == "legislation":
                    results["legislation"] = self.search_legislation(query, top_k, retriever_type)
                else:
                    logger.warning(f"Unknown collection in list: {collection}")
            return results
        
        else:
            raise ValueError(f"Invalid collections parameter: {collections}")
    
    def _search_collection(
        self, 
        query: str, 
        collection_type: str,
        top_k: int = None,
        retriever_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Internal method to search a specific collection.
        
        Args:
            query: Search query string
            collection_type: Type of collection to search
            top_k: Number of results to return
            retriever_type: Type of retriever to use
            
        Returns:
            List of SearchResult objects
        """
        try:
            # Switch to the target collection if needed
            if self.current_collection_type != collection_type:
                self.retriever.switch_collection(collection_type)
                self.current_collection_type = collection_type
                logger.debug(f"Switched to collection: {collection_type}")
            
            # Get collection info for metadata
            collection_info = self.retriever.get_collection_info()
            
            # Check if collection has documents
            if collection_info.get("document_count", 0) == 0:
                logger.warning(f"Collection {collection_type} has no documents")
                return []
            
            # Perform the search using the specified retriever type
            nodes = self.retriever.retrieve_nodes(query, retriever_type)
            
            # Limit results if top_k is specified
            actual_top_k = top_k or self.top_n_rerank
            nodes = nodes[:actual_top_k]
            
            # Convert nodes to SearchResult objects
            results = []
            for node in nodes:
                result = SearchResult(
                    content=node.text if hasattr(node, 'text') else str(node),
                    score=node.score if hasattr(node, 'score') else 0.0,
                    source_collection=collection_info["collection_name"],
                    collection_type=collection_type,
                    metadata={
                        "node_id": node.node_id if hasattr(node, 'node_id') else None,
                        "retriever_type": retriever_type,
                        "query": query
                    }
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} results in {collection_type} collection")
            return results
            
        except Exception as e:
            logger.error(f"Error searching collection {collection_type}: {e}")
            return []
    
    def get_formatted_results(
        self, 
        results: Union[List[SearchResult], Dict[str, List[SearchResult]]],
        include_scores: bool = True,
        max_content_length: int = None,
        query_type: str = "comprehensive"
    ) -> str:
        """
        Format search results for display.
        
        Args:
            results: Search results from run_search()
            include_scores: Whether to include relevance scores
            max_content_length: Maximum length of content to display
            
        Returns:
            Formatted string representation of results
        """
        # Dynamic content length for different legal research needs
        if max_content_length is None:
            length_configs = {
                "quick_reference": 600,      # Quick legal lookups
                "comprehensive": 1200,       # Standard legal research (recommended default)
                "detailed_analysis": 1800,   # Complex legal analysis
                "case_brief": 800,          # Case summaries
                "statute_lookup": 1000      # Legislative research
            }
            max_content_length = length_configs.get(query_type, 1200)
            
        if isinstance(results, list):
            # Single collection results
            return self._format_single_collection_results(
                results, include_scores, max_content_length
            )
        
        elif isinstance(results, dict):
            # Multiple collection results
            formatted_parts = []
            for collection_type, collection_results in results.items():
                if collection_results:
                    formatted_parts.append(f"\n=== {collection_type.upper()} RESULTS ===")
                    formatted_part = self._format_single_collection_results(
                        collection_results, include_scores, max_content_length
                    )
                    formatted_parts.append(formatted_part)
                else:
                    formatted_parts.append(f"\n=== {collection_type.upper()} RESULTS ===")
                    formatted_parts.append("No results found.")
            
            return "\n".join(formatted_parts)
        
        else:
            return "Invalid results format"
    
    def _format_single_collection_results(
        self, 
        results: List[SearchResult],
        include_scores: bool,
        max_content_length: int
    ) -> str:
        """Format results from a single collection."""
        if not results:
            return "No results found."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            content = result.content
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            if include_scores:
                formatted_results.append(
                    f"{i}. [Score: {result.score:.3f}] {content}"
                )
            else:
                formatted_results.append(f"{i}. {content}")
        
        return "\n".join(formatted_results)
    
    def get_collection_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all available collections.
        
        Returns:
            Dictionary with collection statistics
        """
        stats = {}
        
        # Get stats for legal cases
        try:
            self.retriever.switch_collection("legal_cases")
            legal_info = self.retriever.get_collection_info()
            stats["legal_cases"] = legal_info
        except Exception as e:
            stats["legal_cases"] = {"error": str(e)}
        
        # Get stats for legislation
        try:
            self.retriever.switch_collection("legislation")
            legislation_info = self.retriever.get_collection_info()
            stats["legislation"] = legislation_info
        except Exception as e:
            stats["legislation"] = {"error": str(e)}
        
        return stats
    
    def cleanup(self):
        """
        Clean up resources and free memory.
        Should be called when the VectorSearch instance is no longer needed.
        """
        try:
            # Clean up the retriever if it has cleanup methods
            if hasattr(self.retriever, 'cleanup'):
                self.retriever.cleanup()
            
            # Clear references
            self.retriever = None
            
            logger.info("VectorSearch cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during VectorSearch cleanup: {e}")