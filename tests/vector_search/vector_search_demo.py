"""
Example usage of the VectorSearch tool for legal cases and legislation
"""
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.src.tools.vector_search import VectorSearch, SearchResult
from llama_index.core import Document

def demonstrate_vector_search():
    """Demonstrate the VectorSearch tool capabilities"""
    
    print("=== Vector Search Tool Demo ===\n")
    
    # Initialize the search tool
    print("1. Initializing VectorSearch tool...")
    search_tool = VectorSearch(
        similarity_top_k=10,
        top_n_rerank=5
    )
    print("✓ VectorSearch initialized")
    
    # Get collection statistics
    print("\n2. Checking collection statistics...")
    stats = search_tool.get_collection_stats()
    for collection_type, info in stats.items():
        print(f"   {collection_type}: {info.get('document_count', 'unknown')} documents")
    
    # Example search queries
    queries = [
        "contract breach remedies",
        "traffic speed limit violations", 
        "workplace safety regulations"
    ]
    
    print("\n3. Demonstrating different search methods...")
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: '{query}' ---")
        
        # Search all collections
        print(f"\nSearching all collections for: {query}")
        all_results = search_tool.run_search(query, collections="all", top_k=3)
        
        if isinstance(all_results, dict):
            for collection_type, results in all_results.items():
                print(f"\n{collection_type.upper()} Results:")
                if results:
                    for j, result in enumerate(results[:2], 1):  # Show top 2
                        content_preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
                        print(f"  {j}. [Score: {result.score:.3f}] {content_preview}")
                else:
                    print("  No results found")
        
        # Break after first query for demo (since collections might be empty)
        if i == 1:
            break
    
    return search_tool

def example_usage_patterns():
    """Show different usage patterns for the VectorSearch tool"""
    
    print("\n=== Usage Pattern Examples ===\n")
    
    # Initialize search tool
    search_tool = VectorSearch()
    
    print("1. Single collection search:")
    print("   # Search only legal cases")
    print("   legal_results = search_tool.search_legal_cases('contract disputes')")
    print("   ")
    print("   # Search only legislation")  
    print("   legislation_results = search_tool.search_legislation('speed limits')")
    
    print("\n2. Multi-collection search:")
    print("   # Search all collections")
    print("   all_results = search_tool.run_search('contract law', collections='all')")
    print("   ")
    print("   # Search specific collections")
    print("   results = search_tool.run_search('traffic', collections=['legal_cases', 'legislation'])")
    
    print("\n3. Different retriever types:")
    print("   # Use vector similarity only")
    print("   vector_results = search_tool.run_search('query', retriever_type='vector')")
    print("   ")
    print("   # Use BM25 keyword search only")
    print("   bm25_results = search_tool.run_search('query', retriever_type='bm25')")
    print("   ")
    print("   # Use hybrid approach (default)")
    print("   hybrid_results = search_tool.run_search('query', retriever_type='hybrid')")
    
    print("\n4. Formatted output:")
    print("   results = search_tool.run_search('contract law')")
    print("   formatted = search_tool.get_formatted_results(results)")
    print("   print(formatted)")
    
    print("\n5. Collection statistics:")
    print("   stats = search_tool.get_collection_stats()")
    print("   print(f'Legal cases: {stats[\"legal_cases\"][\"document_count\"]} documents')")

def create_sample_documents_for_testing():
    """Create sample documents to test the search functionality"""
    
    print("\n=== Creating Sample Documents for Testing ===\n")
    
    # Initialize search tool
    search_tool = VectorSearch()
    
    # Sample legal case documents
    legal_docs = [
        Document(text="Case 1: Contract breach dispute between ABC Corp and XYZ Ltd. The plaintiff claims damages of $50,000 for failure to deliver goods as per the signed agreement. The court found that the defendant breached the contract by failing to meet delivery deadlines."),
        Document(text="Case 2: Traffic violation case involving speeding in a school zone. The defendant was caught driving 45 mph in a 25 mph zone. The court imposed a fine of $200 and suspended the license for 30 days."),
        Document(text="Case 3: Personal injury claim from a workplace accident. The plaintiff suffered back injuries due to inadequate safety equipment. The employer was found liable and ordered to pay $75,000 in compensation."),
        Document(text="Case 4: Property damage lawsuit after a car accident. The defendant ran a red light and collided with the plaintiff's vehicle, causing $15,000 in damages. Insurance coverage was disputed."),
        Document(text="Case 5: Employment discrimination case based on age. The plaintiff was terminated shortly before retirement eligibility. The court awarded back pay and reinstatement.")
    ]
    
    # Sample legislation documents
    legislation_docs = [
        Document(text="Traffic Safety Act Section 101: Speed limits in residential areas shall not exceed 25 mph during school hours. Violations result in fines of $150-$300 and possible license suspension."),
        Document(text="Consumer Protection Act Section 205: Breach of contract remedies include monetary damages, specific performance, or contract cancellation. Damages must be foreseeable and directly related to the breach."),
        Document(text="Workplace Safety Regulation 15.3: Employers must provide adequate safety equipment including hard hats, safety glasses, and protective footwear. Failure to comply results in fines up to $10,000."),
        Document(text="Motor Vehicle Code Section 42: Running a red light is a Class B traffic violation punishable by fines of $200-$500 and 3 points on driving record."),
        Document(text="Employment Standards Act Section 78: Age discrimination in hiring or termination is prohibited. Violations result in reinstatement and back pay for affected employees.")
    ]
    
    try:
        # Ingest legal case documents
        print("Ingesting legal case documents...")
        search_tool.retriever.switch_collection("legal_cases")
        search_tool.retriever.ingest_documents(legal_docs)
        print(f"✓ Ingested {len(legal_docs)} legal case documents")
        
        # Ingest legislation documents
        print("Ingesting legislation documents...")
        search_tool.retriever.switch_collection("legislation")
        search_tool.retriever.ingest_documents(legislation_docs)
        print(f"✓ Ingested {len(legislation_docs)} legislation documents")
        
        return search_tool
        
    except Exception as e:
        print(f"✗ Error creating sample documents: {e}")
        return None

def test_search_functionality(search_tool):
    """Test the search functionality with sample documents"""
    
    print("\n=== Testing Search Functionality ===\n")
    
    test_queries = [
        "contract breach damages",
        "traffic speed limit violations",
        "workplace safety equipment"
    ]
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        
        # Test search across all collections
        results = search_tool.run_search(query, collections="all", top_k=2)
        formatted_results = search_tool.get_formatted_results(results)
        
        print(formatted_results)
        print("-" * 50)

if __name__ == "__main__":
    # Note: This requires the models to be downloaded and sufficient memory
    print("VectorSearch Tool Demo")
    print("Note: This demo requires embedding models to be downloaded")
    print("Ensure you have sufficient memory (4-8GB) and a stable internet connection\n")
    
    # Show usage patterns (lightweight)
    example_usage_patterns()
    
    # Option to run full demo with model loading
    print("\n" + "="*60)
    print("To run the full demo with actual model loading and document ingestion:")
    print("Uncomment the lines below and ensure you have the required dependencies:")
    print("pip install chromadb llama-index[all]")
    print("="*60)
    
    # Uncomment these lines to run the full demo:
    # search_tool = create_sample_documents_for_testing()
    # if search_tool:
    #     test_search_functionality(search_tool)
    #     demonstrate_vector_search()
