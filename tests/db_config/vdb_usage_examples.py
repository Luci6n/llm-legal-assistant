"""
Example usage of HybridVDBRetriever with db_config integration
"""
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Example 1: Basic usage with config defaults
def example_basic_usage():
    """Basic usage example using configuration defaults"""
    from app.api.src.storage.vdb_handler import HybridVDBRetriever
    
    # Create retriever for legal cases - uses config automatically
    legal_retriever = HybridVDBRetriever(
        collection_type="legal_cases"  # Maps to configured collection name
    )
    
    # Create retriever for legislation - uses config automatically  
    legislation_retriever = HybridVDBRetriever(
        collection_type="legislation"  # Maps to configured collection name
    )
    
    return legal_retriever, legislation_retriever

# Example 2: Custom configuration override
def example_custom_config():
    """Example with custom configuration overrides"""
    from app.api.src.storage.vdb_handler import HybridVDBRetriever
    
    # Override specific config values while keeping others
    custom_retriever = HybridVDBRetriever(
        collection_type="legal_cases",
        chroma_path="./my_custom_vectordb",      # Override default path
        collection_name="my_legal_cases",       # Override default collection name
        similarity_top_k=50                     # Custom retrieval settings
    )
    
    return custom_retriever

# Example 3: Environment-based configuration
def example_env_config():
    """Example showing how to configure via environment variables"""
    
    # You can set these in your .env file:
    # CHROMA_PERSIST_DIR=./production_vectordb
    # CHROMA_LEGAL_CASES_COLLECTION=prod_legal_cases
    # CHROMA_LEGISLATION_COLLECTION=prod_legislation
    # CHROMA_HOST=your-remote-server.com
    # CHROMA_PORT=8001
    
    from app.api.src.storage.vdb_handler import HybridVDBRetriever
    
    # This will automatically use environment variables
    retriever = HybridVDBRetriever(
        collection_type="legal_cases"
    )
    
    return retriever

# Example 4: Remote ChromaDB server
def example_remote_chroma():
    """Example for using remote ChromaDB server"""
    
    # Set in .env file:
    # CHROMA_HOST=remote-chroma-server.com
    # CHROMA_PORT=8000
    # CHROMA_PERSIST_DIR=  # Leave empty for remote mode
    
    from app.api.src.storage.vdb_handler import HybridVDBRetriever
    
    retriever = HybridVDBRetriever(
        collection_type="legal_cases"
    )
    
    return retriever

# Example 5: Full workflow with documents
def example_full_workflow():
    """Complete example with document ingestion and querying"""
    from app.api.src.storage.vdb_handler import HybridVDBRetriever
    from llama_index.core import Document
    
    # Create retriever
    retriever = HybridVDBRetriever(
        collection_type="legal_cases",
        similarity_top_k=20,  # Retrieve top 20 similar documents
        top_n_rerank=10       # Rerank top 10 for final results
    )
    
    # Prepare documents
    documents = [
        Document(text="Legal case about contract breach and damages..."),
        Document(text="Traffic violation case with speed limit analysis..."),
        Document(text="Personal injury claim in workplace accident...")
    ]
    
    # Ingest documents
    retriever.ingest_documents(documents)
    
    # Query the system
    response = retriever.query("What are the damages for contract breach?")
    
    # Or retrieve nodes directly for more control
    nodes = retriever.retrieve_nodes("contract breach", retriever_type="hybrid")
    
    return retriever, response, nodes

if __name__ == "__main__":
    print("=== VDB Handler Usage Examples ===\n")
    
    print("1. Basic usage with config defaults:")
    print("   legal_retriever = HybridVDBRetriever(collection_type='legal_cases')")
    print("   legislation_retriever = HybridVDBRetriever(collection_type='legislation')")
    
    print("\n2. Custom configuration override:")
    print("   custom_retriever = HybridVDBRetriever(")
    print("       collection_type='legal_cases',")
    print("       chroma_path='./my_custom_vectordb',")
    print("       collection_name='my_legal_cases'")
    print("   )")
    
    print("\n3. Environment-based configuration:")
    print("   Set in .env file:")
    print("   CHROMA_PERSIST_DIR=./production_vectordb")
    print("   CHROMA_LEGAL_CASES_COLLECTION=prod_legal_cases")
    print("   CHROMA_LEGISLATION_COLLECTION=prod_legislation")
    
    print("\n4. Remote ChromaDB server:")
    print("   Set in .env file:")
    print("   CHROMA_HOST=remote-server.com")
    print("   CHROMA_PORT=8000")
    print("   CHROMA_PERSIST_DIR=  # Leave empty")
    
    print("\n5. Key benefits of the configuration integration:")
    print("   ✓ Centralized configuration in db_config.py")
    print("   ✓ Environment variable support via .env")
    print("   ✓ Automatic local vs remote detection")
    print("   ✓ Collection type mapping")
    print("   ✓ Easy override capability")
    print("   ✓ Consistent configuration across the application")
