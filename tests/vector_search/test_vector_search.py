"""
Quick test of VectorSearch tool with sample data
"""
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.src.tools.vector_search import VectorSearch, SearchResult
from llama_index.core import Document

def quick_vector_search_test():
    """Quick test of the VectorSearch functionality"""
    
    print("=== Quick VectorSearch Test ===\n")
    
    # Initialize search tool
    print("Initializing VectorSearch...")
    search_tool = VectorSearch(similarity_top_k=10, top_n_rerank=5)
    print("✓ VectorSearch initialized")
    
    # Check initial collection statistics
    print("\nChecking collection statistics...")
    stats = search_tool.get_collection_stats()
    
    for collection_type, info in stats.items():
        if 'error' in info:
            print(f"   {collection_type}: Error - {info['error']}")
        else:
            print(f"   {collection_type}: {info.get('document_count', 0)} documents")
    
    # Test collection switching
    print("\nTesting collection switching...")
    try:
        # Switch to legal cases
        search_tool.retriever.switch_collection("legal_cases")
        info = search_tool.retriever.get_collection_info()
        print(f"✓ Switched to: {info['collection_name']} ({info['document_count']} documents)")
        
        # Switch to legislation
        search_tool.retriever.switch_collection("legislation")
        info = search_tool.retriever.get_collection_info()
        print(f"✓ Switched to: {info['collection_name']} ({info['document_count']} documents)")
        
    except Exception as e:
        print(f"✗ Error during collection switching: {e}")
    
    print("\n=== VectorSearch Tool Ready for Use ===")
    print("Available methods:")
    print("- search_tool.search_legal_cases(query)")
    print("- search_tool.search_legislation(query)")  
    print("- search_tool.run_search(query, collections='all')")
    print("- search_tool.get_collection_stats()")
    
    return search_tool

if __name__ == "__main__":
    search_tool = quick_vector_search_test()
