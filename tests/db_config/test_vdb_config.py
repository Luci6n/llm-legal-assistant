"""
Test script to demonstrate using HybridVDBRetriever with db_config configuration
"""
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.api.src.storage.vdb_handler import HybridVDBRetriever
from app.api.src.storage.db_config import db_config
from llama_index.core import Document

def test_config_integration():
    """Test the integration between vdb_handler and db_config"""
    
    print("=== Testing VDB Handler with DB Config ===\n")
    
    # Display current configuration
    print("Current ChromaDB Configuration:")
    print(f"  Host: {db_config.chroma.host}")
    print(f"  Port: {db_config.chroma.port}")
    print(f"  Persist Directory: {db_config.chroma.persist_directory}")
    print(f"  Collections: {db_config.chroma.collections}")
    print(f"  Client Settings: {db_config.chroma.client_settings}")
    
    print("\n=== Creating Retrievers (One at a Time) ===\n")
    
    # 1. Create retriever for legal cases using config defaults
    print("1. Creating legal cases retriever (uses config defaults)...")
    try:
        legal_cases_retriever = HybridVDBRetriever(
            collection_type="legal_cases"
        )
        print(f"   ✓ Collection: {legal_cases_retriever.collection_name}")
        print(f"   ✓ ChromaDB Path: {legal_cases_retriever.chroma_path}")
        print(f"   ✓ Device: {legal_cases_retriever.device}")
        
        # Clean up resources
        print("   → Cleaning up legal cases retriever...")
        del legal_cases_retriever
        import gc
        gc.collect()
        print("   ✓ Legal cases retriever cleaned up")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 2. Create retriever for legislation using config defaults
    print("\n2. Creating legislation retriever (uses config defaults)...")
    try:
        legislation_retriever = HybridVDBRetriever(
            collection_type="legislation"
        )
        print(f"   ✓ Collection: {legislation_retriever.collection_name}")
        print(f"   ✓ ChromaDB Path: {legislation_retriever.chroma_path}")
        print(f"   ✓ Device: {legislation_retriever.device}")
        
        # Clean up resources
        print("   → Cleaning up legislation retriever...")
        del legislation_retriever
        gc.collect()
        print("   ✓ Legislation retriever cleaned up")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 3. Create retriever with custom overrides
    print("\n3. Creating custom retriever (overrides config)...")
    try:
        custom_retriever = HybridVDBRetriever(
            collection_type="legal_cases",
            chroma_path="./custom_chroma_path",
            collection_name="custom_collection"
        )
        print(f"   ✓ Collection: {custom_retriever.collection_name}")
        print(f"   ✓ ChromaDB Path: {custom_retriever.chroma_path}")
        print(f"   ✓ Device: {custom_retriever.device}")
        
        # Clean up resources
        print("   → Cleaning up custom retriever...")
        del custom_retriever
        gc.collect()
        print("   ✓ Custom retriever cleaned up")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== Configuration Benefits ===")
    print("✓ Centralized configuration in db_config.py")
    print("✓ Environment variable support via .env file")
    print("✓ Automatic local vs remote ChromaDB detection")
    print("✓ Collection name mapping based on type")
    print("✓ Override capability for custom use cases")
    print("✓ Proper resource cleanup between retrievers")
    
    return True

def test_single_retriever_multiple_collections():
    """Test using a single retriever for multiple collections"""
    
    print("=== Testing Single Retriever with Multiple Collections ===\n")
    
    # Display current configuration
    print("Current ChromaDB Configuration:")
    print(f"  Host: {db_config.chroma.host}")
    print(f"  Port: {db_config.chroma.port}")
    print(f"  Persist Directory: {db_config.chroma.persist_directory}")
    print(f"  Collections: {db_config.chroma.collections}")
    print(f"  Client Settings: {db_config.chroma.client_settings}")
    
    print("\n=== Creating Single Retriever and Switching Collections ===\n")
    
    try:
        # Create one retriever initially for legal cases
        print("1. Creating retriever for legal cases...")
        retriever = HybridVDBRetriever(collection_type="legal_cases")
        
        # Display initial collection info
        info = retriever.get_collection_info()
        print(f"   ✓ Initial Collection: {info['collection_name']}")
        print(f"   ✓ Collection Type: {info['collection_type']}")
        print(f"   ✓ ChromaDB Path: {info['chroma_path']}")
        print(f"   ✓ Device: {info['device']}")
        print(f"   ✓ Document Count: {info['document_count']}")
        
        # Switch to legislation collection
        print("\n2. Switching to legislation collection...")
        retriever.switch_collection("legislation")
        
        # Display updated collection info
        info = retriever.get_collection_info()
        print(f"   ✓ New Collection: {info['collection_name']}")
        print(f"   ✓ Collection Type: {info['collection_type']}")
        print(f"   ✓ Document Count: {info['document_count']}")
        
        # Switch to custom collection
        print("\n3. Switching to custom collection...")
        retriever.switch_collection("legal_cases", "custom_legal_collection")
        
        # Display custom collection info
        info = retriever.get_collection_info()
        print(f"   ✓ Custom Collection: {info['collection_name']}")
        print(f"   ✓ Collection Type: {info['collection_type']}")
        print(f"   ✓ Document Count: {info['document_count']}")
        
        # Switch back to original
        print("\n4. Switching back to original legal cases collection...")
        retriever.switch_collection("legal_cases")
        
        # Display final collection info
        info = retriever.get_collection_info()
        print(f"   ✓ Back to Collection: {info['collection_name']}")
        print(f"   ✓ Collection Type: {info['collection_type']}")
        print(f"   ✓ Document Count: {info['document_count']}")
        
        print("\n=== Benefits of Single Retriever Approach ===")
        print("✓ Models loaded only once (saves memory and time)")
        print("✓ Can switch between collections without reinitializing")
        print("✓ Embedding model and reranker are reused")
        print("✓ Only vector store and collection references change")
        print("✓ Much more efficient for multi-collection workflows")
        
        # Clean up resources
        print("\n   → Cleaning up retriever...")
        del retriever
        import gc
        gc.collect()
        print("   ✓ Retriever cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
def test_document_ingestion():
    """Test document ingestion with collection switching"""
    print("\n=== Testing Document Ingestion with Collection Switching ===\n")
    
    try:
        # Create a single retriever
        print("Creating retriever for document ingestion test...")
        retriever = HybridVDBRetriever(collection_type="legal_cases")
        
        # Test with legal cases documents
        legal_docs = [
            Document(text="This is a sample legal case about traffic violations and speeding tickets."),
            Document(text="Contract law principles and breach of contract remedies."),
            Document(text="Personal injury claims in automobile accidents.")
        ]
        
        print(f"Ingesting {len(legal_docs)} legal documents...")
        retriever.ingest_documents(legal_docs)
        print("✓ Legal documents ingested successfully")
        
        # Test querying legal cases
        print("\nTesting query on legal cases...")
        response = retriever.query("What are the remedies for contract breach?")
        print(f"✓ Legal query response: {response[:100]}...")
        
        # Switch to legislation collection
        print("\nSwitching to legislation collection...")
        retriever.switch_collection("legislation")
        
        # Test with legislation documents
        legislation_docs = [
            Document(text="Traffic Safety Act Section 101: Speed limit regulations and enforcement."),
            Document(text="Consumer Protection Act: Rights and remedies for breach of contract."),
            Document(text="Employment Standards Act: Workplace safety and compensation laws.")
        ]
        
        print(f"Ingesting {len(legislation_docs)} legislation documents...")
        retriever.ingest_documents(legislation_docs)
        print("✓ Legislation documents ingested successfully")
        
        # Test querying legislation
        print("\nTesting query on legislation...")
        response = retriever.query("What are the speed limit regulations?")
        print(f"✓ Legislation query response: {response[:100]}...")
        
        # Clean up
        print("\n   → Cleaning up retriever...")
        del retriever
        import gc
        gc.collect()
        print("   ✓ Retriever cleaned up successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Missing dependencies: {e}")
        print("  Install with: pip install chromadb llama-index")
        return False
    except Exception as e:
        print(f"✗ Error during ingestion test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    # Check command line arguments for test type
    test_type = "single"  # Default to single retriever test
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    
    print("Available test options:")
    print("  python test_vdb_config.py single    - Test single retriever with multiple collections (recommended)")
    print("  python test_vdb_config.py full      - Test all retrievers sequentially") 
    print("  python test_vdb_config.py ingest    - Test document ingestion with collection switching")
    print(f"\nRunning test type: {test_type}\n")
    
    if test_type == "full":
        # Test configuration integration with all retrievers
        config_test_passed = test_config_integration()
    elif test_type == "ingest":
        # Test document ingestion with collection switching
        single_test_passed = test_single_retriever_multiple_collections()
        if single_test_passed:
            print("\n" + "="*50)
            ingestion_test_passed = test_document_ingestion()
        else:
            print("Skipping ingestion test due to single retriever test failure")
    else:  # default to "single"
        # Test single retriever with multiple collections (most efficient)
        single_test_passed = test_single_retriever_multiple_collections()
    
    print("\n" + "="*50)
    print("Note: For full testing with document ingestion:")
    print("Install with: pip install chromadb llama-index[all]")
    print("="*50)
