"""
Vector Database Retriever with Hybrid Search (BM25 + Vector)
"""

import os
import logging
from typing import List, Optional
from pathlib import Path

import torch
import chromadb
from dotenv import load_dotenv

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridVDBRetriever:
    """
    A hybrid retriever that combines vector similarity search with BM25 keyword search.
    """
    
    def __init__(
        self,
        embed_model_name: str = "BAAI/bge-m3",
        rerank_model_name: str = "BAAI/bge-reranker-large",
        chroma_path: str = "./legal_cases", # "./legal_cases" or "./data/legislation"
        collection_name: str = "fyp1",
        device: "cuda" | "cpu" | None = None,
        top_n_rerank: int = 40,
        similarity_top_k: int = 100
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            embed_model_name: Name of the embedding model
            rerank_model_name: Name of the reranking model
            chroma_path: Path to ChromaDB storage
            collection_name: Name of the collection
            device: Device to use (cuda/cpu), auto-detected if None
            top_n_rerank: Number of documents to rerank
            similarity_top_k: Number of similar documents to retrieve
        """
        load_dotenv()
        
        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.similarity_top_k = similarity_top_k
        
        # Initialize models
        self._initialize_models(embed_model_name, rerank_model_name, top_n_rerank)
        
        # Initialize vector store
        self._initialize_vector_store()
        
        # Initialize retrievers (will be set after ingestion)
        self.vector_retriever = None
        self.bm25_retriever = None
        self.hybrid_retriever = None
        self.query_engine = None
        
        logger.info(f"HybridVDBRetriever initialized on {self.device}")
    
    def _initialize_models(self, embed_model_name: str, rerank_model_name: str, top_n_rerank: int):
        """Initialize embedding and reranking models."""
        try:
            self.embed_model = HuggingFaceEmbedding(
                model_name=embed_model_name,
                device=self.device
            )
            
            self.reranker = FlagEmbeddingReranker(
                model=rerank_model_name,
                top_n=top_n_rerank
            )
            
            # Set global embedding model
            Settings.embed_model = self.embed_model
            
            logger.info("Embedding model and reranker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store."""
        try:
            # Create directory if it doesn't exist
            Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            self.vector_store = ChromaVectorStore(
                chroma_collection=self.collection,
                embed_model=self.embed_model
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _create_ingestion_pipeline(self) -> IngestionPipeline:
        """Create the ingestion pipeline with semantic splitting."""
        splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=self.embed_model
        )
        
        return IngestionPipeline(
            transformations=[splitter, self.embed_model],
            vector_store=self.vector_store,
        )
    
    def ingest_documents(self, documents: List[Document]) -> None:
        """
        Ingest documents into the vector store and prepare retrievers.
        
        Args:
            documents: List of Document objects to ingest
        """
        if not documents:
            logger.warning("No documents provided for ingestion")
            return
        
        try:
            # Run ingestion pipeline
            pipeline = self._create_ingestion_pipeline()
            pipeline.run(documents=documents)
            logger.info(f"Ingested {len(documents)} documents successfully")
            
            # Create index and retrievers
            self._setup_retrievers(documents)
            
        except Exception as e:
            logger.error(f"Failed to ingest documents: {e}")
            raise
    
    def _setup_retrievers(self, documents: List[Document]) -> None:
        """Setup vector and BM25 retrievers after ingestion."""
        try:
            # Create vector index and retriever
            self.index = VectorStoreIndex.from_vector_store(self.vector_store)
            self.vector_retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=self.similarity_top_k
            )
            
            # Create BM25 retriever
            self.bm25_retriever = BM25Retriever.from_defaults(
                docstore=self.index.docstore,
                similarity_top_k=self.similarity_top_k
            )
            
            # Create hybrid retriever using query fusion
            self.hybrid_retriever = QueryFusionRetriever(
                retrievers=[self.vector_retriever, self.bm25_retriever],
                similarity_top_k=self.similarity_top_k,
                num_queries=1,  # No query generation, use original query
            )
            
            # Create query engine with reranking
            self.query_engine = RetrieverQueryEngine(
                retriever=self.hybrid_retriever,
                node_postprocessors=[self.reranker]
            )
            
            logger.info("Retrievers and query engine setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup retrievers: {e}")
            raise
    
    def query(self, query_text: str) -> str:
        """
        Query the hybrid retriever.
        
        Args:
            query_text: The query string
            
        Returns:
            Response string from the query engine
        """
        if self.query_engine is None:
            raise ValueError("No documents have been ingested yet. Call ingest_documents() first.")
        
        try:
            response = self.query_engine.query(query_text)
            return str(response)
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def retrieve_nodes(self, query_text: str, retriever_type: str = "hybrid"):
        """
        Retrieve nodes using specified retriever type.
        
        Args:
            query_text: The query string
            retriever_type: "hybrid", "vector", or "bm25"
            
        Returns:
            List of retrieved nodes
        """
        if retriever_type == "hybrid" and self.hybrid_retriever:
            return self.hybrid_retriever.retrieve(query_text)
        elif retriever_type == "vector" and self.vector_retriever:
            return self.vector_retriever.retrieve(query_text)
        elif retriever_type == "bm25" and self.bm25_retriever:
            return self.bm25_retriever.retrieve(query_text)
        else:
            raise ValueError(f"Invalid retriever type: {retriever_type} or retriever not initialized")


def main():
    """Example usage of the HybridVDBRetriever."""
    # Initialize retriever
    retriever = HybridVDBRetriever(
        chroma_path="./data/chroma_db",
        collection_name="legal_docs"
    )
    
    # Example documents (replace with your actual documents)
    documents = [
        Document(text="Sample legal document about car accidents and insurance claims."),
        Document(text="Traffic law regulations and penalty guidelines."),
        # Add your actual documents here
    ]
    
    # Ingest documents
    retriever.ingest_documents(documents)
    
    # Query the system
    response = retriever.query("Is there anything related to car accidents?")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()