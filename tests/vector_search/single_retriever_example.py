"""
Example: Using a Single HybridVDBRetriever for Multiple Collections
This demonstrates the most efficient approach for working with multiple collections.
"""
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.src.storage.vdb_handler import HybridVDBRetriever
from app.api.src.storage.db_config import db_config
from llama_index.core import Document

def single_retriever_workflow():
    """
    Demonstrates using a single retriever for multiple collections.
    This is much more memory and time efficient than creating separate retrievers.
    """
    
    print("=== Single Retriever Multi-Collection Workflow ===\n")
    
    # Create ONE retriever that will be used for all collections
    print("Creating single retriever (models loaded once)...")
    retriever = HybridVDBRetriever(
        collection_type="legal_cases",  # Start with legal cases
        similarity_top_k=20
    )
    print(f"✓ Retriever created for: {retriever.collection_name}")
    
    # === Work with Legal Cases ===
    print("\n1. Working with Legal Cases Collection:")
    
    # Add some legal case documents
    legal_docs = [
        Document(text="Case 1: Traffic accident involving speeding and negligent driving."),
        Document(text="Case 2: Contract dispute over breach of service agreement."),
        Document(text="Case 3: Personal injury claim from workplace accident.")
    ]
    
    retriever.ingest_documents(legal_docs)
    print(f"   ✓ Ingested {len(legal_docs)} legal case documents")
    
    # Query legal cases
    response = retriever.query("What cases involve contract disputes?")
    print(f"   ✓ Query result: {response[:80]}...")
    
    # === Switch to Legislation ===
    print("\n2. Switching to Legislation Collection:")
    retriever.switch_collection("legislation")  # Models stay loaded!
    print(f"   ✓ Switched to: {retriever.collection_name}")
    
    # Add legislation documents
    legislation_docs = [
        Document(text="Traffic Safety Act: Speed limits and enforcement procedures."),
        Document(text="Consumer Protection Act: Contract law and breach remedies."),
        Document(text="Employment Standards Act: Workplace safety requirements.")
    ]
    
    retriever.ingest_documents(legislation_docs)
    print(f"   ✓ Ingested {len(legislation_docs)} legislation documents")
    
    # Query legislation
    response = retriever.query("What are the speed limit regulations?")
    print(f"   ✓ Query result: {response[:80]}...")
    
    # === Switch to Custom Collection ===
    print("\n3. Switching to Custom Collection:")
    retriever.switch_collection("legal_cases", "research_collection")
    print(f"   ✓ Switched to custom: {retriever.collection_name}")
    
    # Add research documents
    research_docs = [
        Document(text="Legal research: Analysis of contract law evolution."),
        Document(text="Academic paper: Traffic law enforcement effectiveness."),
        Document(text="Study: Personal injury claim settlement patterns.")
    ]
    
    retriever.ingest_documents(research_docs)
    print(f"   ✓ Ingested {len(research_docs)} research documents")
    
    # === Collection Information ===
    print("\n4. Collection Information:")
    
    # Switch back to legal cases and show info
    retriever.switch_collection("legal_cases")
    info = retriever.get_collection_info()
    print(f"   Legal Cases: {info['document_count']} documents")
    
    # Switch to legislation and show info
    retriever.switch_collection("legislation")
    info = retriever.get_collection_info()
    print(f"   Legislation: {info['document_count']} documents")
    
    # Switch to custom and show info
    retriever.switch_collection("legal_cases", "research_collection")
    info = retriever.get_collection_info()
    print(f"   Research: {info['document_count']} documents")
    
    print("\n=== Efficiency Benefits ===")
    print("✓ Embedding model loaded only once")
    print("✓ Reranker model loaded only once")
    print("✓ Fast collection switching")
    print("✓ Minimal memory overhead")
    print("✓ Reuse of expensive model initialization")
    
    return retriever

def multi_collection_search_example():
    """
    Example of searching across multiple collections efficiently.
    """
    
    print("\n=== Multi-Collection Search Example ===\n")
    
    # Use the retriever from the previous workflow
    retriever = single_retriever_workflow()
    
    query = "contract breach"
    results = {}
    
    # Search in each collection
    collections_to_search = [
        ("legal_cases", None),
        ("legislation", None),
        ("legal_cases", "research_collection")
    ]
    
    print(f"\nSearching for '{query}' across all collections:")
    
    for collection_type, custom_name in collections_to_search:
        # Switch to collection
        retriever.switch_collection(collection_type, custom_name)
        collection_name = retriever.collection_name
        
        try:
            # Perform search
            nodes = retriever.retrieve_nodes(query, retriever_type="hybrid")
            results[collection_name] = len(nodes)
            print(f"   {collection_name}: {len(nodes)} relevant documents found")
        except ValueError:
            # Collection might not have documents ingested yet
            results[collection_name] = "No documents ingested"
            print(f"   {collection_name}: No documents ingested yet")
    
    print(f"\n✓ Search completed across {len(collections_to_search)} collections")
    return results

def configuration_examples():
    """
    Show different ways to configure the single retriever approach.
    """
    
    print("\n=== Configuration Examples ===\n")
    
    print("1. Basic configuration (uses db_config defaults):")
    print("   retriever = HybridVDBRetriever(collection_type='legal_cases')")
    print(f"   → Would use collection: {db_config.chroma.collections['legal_cases']}")
    print(f"   → Would use path: {db_config.chroma.persist_directory}")
    
    print("\n2. Custom configuration:")
    print("   retriever = HybridVDBRetriever(")
    print("       collection_type='legal_cases',")
    print("       chroma_path='./custom_vectordb',")
    print("       similarity_top_k=10")
    print("   )")
    print("   → Would use custom path and settings")
    
    print("\n3. Environment variables (set in .env):")
    print("   CHROMA_PERSIST_DIR=./production_vectordb")
    print("   CHROMA_LEGAL_CASES_COLLECTION=prod_legal_cases")
    print("   CHROMA_LEGISLATION_COLLECTION=prod_legislation")
    print("   → Automatically picked up by db_config")
    
    print("\n4. Single retriever workflow:")
    print("   # Create once")
    print("   retriever = HybridVDBRetriever(collection_type='legal_cases')")
    print("   ")
    print("   # Switch collections as needed (no model reloading)")
    print("   retriever.switch_collection('legislation')")
    print("   retriever.switch_collection('legal_cases', 'custom_collection')")
    
    return True

if __name__ == "__main__":
    # Show configuration examples (lightweight - no heavy model loading)
    print("=== Single Retriever Multi-Collection Approach ===")
    print("This demonstrates the most efficient way to work with multiple collections.")
    print("Heavy models (embedding & reranking) are loaded only ONCE!\n")
    
    # Show configuration without creating multiple instances
    configuration_examples()
    
    print("\n" + "="*60)
    print("Benefits of Single Retriever Approach:")
    print("✓ Embedding model loaded only once (saves ~2-3GB memory)")
    print("✓ Reranking model loaded only once (saves ~1-2GB memory)")
    print("✓ Fast collection switching (only vector store changes)")
    print("✓ Same models work across all collections")
    print("✓ Ideal for multi-collection workflows")
    print("="*60)
    
    print("\nTo test the actual functionality:")
    print("Run: python test_vdb_config.py single")
    print("     python test_vdb_config.py ingest  (for full workflow test)")
    
    print("\nFor production usage, create ONE retriever and switch collections:")
    print("```python")
    print("retriever = HybridVDBRetriever(collection_type='legal_cases')")
    print("# Work with legal cases...")
    print("retriever.switch_collection('legislation')")
    print("# Work with legislation...")
    print("retriever.switch_collection('legal_cases', 'custom_collection')")
    print("# Work with custom collection...")
    print("```")
