"""
Long-term memory module for the legal assistant.
Handles persistent storage of user preferences, case history, and knowledge.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import os
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
import chromadb
from FlagEmbedding import BGEM3FlagModel


@dataclass
class UserInteraction:
    """Represents a user interaction for long-term storage."""
    timestamp: datetime
    user_input: str
    ai_response: str
    legal_domain: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    satisfaction_score: Optional[float] = None
    topics: Optional[List[str]] = None


@dataclass
class UserProfile:
    """Represents user profile and preferences."""
    user_id: str
    creation_date: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    expertise_level: str  # beginner, intermediate, expert
    legal_domains: List[str]
    interaction_count: int
    satisfaction_avg: Optional[float] = None


class LongTermMemory:
    """
    Manages long-term memory for the legal assistant.
    Stores user profiles, interaction history, and learned knowledge.
    """
    
    def __init__(
        self, 
        storage_path: str = "memory_storage",
        embedding_model_path: str = "BAAI/bge-m3"
    ):
        """
        Initialize long-term memory.
        
        Args:
            storage_path: Path to store memory files
            embedding_model_path: Path or name of BGE-M3 model
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize BGE-M3 model
        self.embedding_model = BGEM3FlagModel(embedding_model_path, use_fp16=True)
        
        # Database for structured data
        self.db_path = self.storage_path / "memory.db"
        self.init_database()
        
        # Initialize Chroma client and collections
        self.chroma_client = chromadb.PersistentClient(path=str(self.storage_path / "chroma_db"))
        
        # Create collections for interactions and knowledge
        self.interaction_collection = self.chroma_client.get_or_create_collection(
            name="interactions",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.knowledge_collection = self.chroma_client.get_or_create_collection(
            name="legal_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
    def init_database(self) -> None:
        """Initialize SQLite database for structured data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    creation_date TEXT,
                    last_active TEXT,
                    preferences TEXT,
                    expertise_level TEXT,
                    legal_domains TEXT,
                    interaction_count INTEGER,
                    satisfaction_avg REAL
                )
            """)
            
            # Interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    timestamp TEXT,
                    user_input TEXT,
                    ai_response TEXT,
                    legal_domain TEXT,
                    case_type TEXT,
                    jurisdiction TEXT,
                    satisfaction_score REAL,
                    topics TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            """)
            
            # Legal concepts learned
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_name TEXT UNIQUE,
                    definition TEXT,
                    legal_domain TEXT,
                    examples TEXT,
                    related_concepts TEXT,
                    frequency_used INTEGER DEFAULT 1,
                    last_accessed TEXT
                )
            """)
            
            conn.commit()
    
    def create_or_update_user_profile(
        self, 
        user_id: str, 
        preferences: Optional[Dict[str, Any]] = None,
        expertise_level: Optional[str] = None,
        legal_domains: Optional[List[str]] = None
    ) -> UserProfile:
        """Create or update user profile."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                updates = []
                params = []
                
                if preferences:
                    updates.append("preferences = ?")
                    params.append(json.dumps(preferences))
                
                if expertise_level:
                    updates.append("expertise_level = ?")
                    params.append(expertise_level)
                
                if legal_domains:
                    updates.append("legal_domains = ?")
                    params.append(json.dumps(legal_domains))
                
                updates.append("last_active = ?")
                params.append(datetime.now().isoformat())
                
                params.append(user_id)
                
                query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(query, params)
                
                # Fetch updated user
                cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
            else:
                # Create new user
                now = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO user_profiles 
                    (user_id, creation_date, last_active, preferences, expertise_level, legal_domains, interaction_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, now, now,
                    json.dumps(preferences or {}),
                    expertise_level or "beginner",
                    json.dumps(legal_domains or []),
                    0
                ))
                
                cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
            
            conn.commit()
            
            # Convert to UserProfile object
            return UserProfile(
                user_id=user_data[0],
                creation_date=datetime.fromisoformat(user_data[1]),
                last_active=datetime.fromisoformat(user_data[2]),
                preferences=json.loads(user_data[3]),
                expertise_level=user_data[4],
                legal_domains=json.loads(user_data[5]),
                interaction_count=user_data[6],
                satisfaction_avg=user_data[7]
            )
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return UserProfile(
                    user_id=user_data[0],
                    creation_date=datetime.fromisoformat(user_data[1]),
                    last_active=datetime.fromisoformat(user_data[2]),
                    preferences=json.loads(user_data[3]),
                    expertise_level=user_data[4],
                    legal_domains=json.loads(user_data[5]),
                    interaction_count=user_data[6],
                    satisfaction_avg=user_data[7]
                )
            return None
    
    def store_interaction(
        self,
        user_id: str,
        user_input: str,
        ai_response: str,
        legal_domain: Optional[str] = None,
        case_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        satisfaction_score: Optional[float] = None,
        topics: Optional[List[str]] = None
    ) -> None:
        """Store user interaction in both database and vector store."""
        interaction = UserInteraction(
            timestamp=datetime.now(),
            user_input=user_input,
            ai_response=ai_response,
            legal_domain=legal_domain,
            case_type=case_type,
            jurisdiction=jurisdiction,
            satisfaction_score=satisfaction_score,
            topics=topics
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO interactions 
                (user_id, timestamp, user_input, ai_response, legal_domain, case_type, 
                 jurisdiction, satisfaction_score, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                interaction.timestamp.isoformat(),
                interaction.user_input,
                interaction.ai_response,
                interaction.legal_domain,
                interaction.case_type,
                interaction.jurisdiction,
                interaction.satisfaction_score,
                json.dumps(interaction.topics) if interaction.topics else None
            ))
            
            # Update user interaction count
            cursor.execute("""
                UPDATE user_profiles 
                SET interaction_count = interaction_count + 1,
                    last_active = ?
                WHERE user_id = ?
            """, (interaction.timestamp.isoformat(), user_id))
            
            conn.commit()
        
        # Store in Chroma vector store for semantic search
        doc_text = f"User: {user_input}\nAssistant: {ai_response}"
        doc_id = str(uuid.uuid4())
        
        # Generate embedding using BGE-M3
        embedding = self.embedding_model.encode([doc_text])['dense_vecs'][0].tolist()
        
        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "timestamp": interaction.timestamp.isoformat(),
            "legal_domain": legal_domain or "general",
            "case_type": case_type or "general",
            "jurisdiction": jurisdiction or "general",
            "topics": json.dumps(topics or [])
        }
        
        # Add satisfaction score if provided
        if satisfaction_score is not None:
            metadata["satisfaction_score"] = satisfaction_score
        
        # Add to Chroma collection
        self.interaction_collection.add(
            embeddings=[embedding],
            documents=[doc_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
    
    def search_similar_interactions(
        self,
        query: str,
        user_id: Optional[str] = None,
        k: int = 5,
        legal_domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar past interactions."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])['dense_vecs'][0].tolist()
        
        # Build where filter
        where_filter = {}
        if user_id:
            where_filter["user_id"] = user_id
        if legal_domain:
            where_filter["legal_domain"] = legal_domain
        
        # Search in Chroma
        if where_filter:
            results = self.interaction_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter
            )
        else:
            results = self.interaction_collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def store_legal_concept(
        self,
        concept_name: str,
        definition: str,
        legal_domain: str,
        examples: Optional[List[str]] = None,
        related_concepts: Optional[List[str]] = None
    ) -> None:
        """Store learned legal concept."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if concept exists
            cursor.execute("SELECT frequency_used FROM learned_concepts WHERE concept_name = ?", (concept_name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency and last accessed
                cursor.execute("""
                    UPDATE learned_concepts 
                    SET frequency_used = frequency_used + 1, last_accessed = ?
                    WHERE concept_name = ?
                """, (datetime.now().isoformat(), concept_name))
            else:
                # Insert new concept
                cursor.execute("""
                    INSERT INTO learned_concepts 
                    (concept_name, definition, legal_domain, examples, related_concepts, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    concept_name,
                    definition,
                    legal_domain,
                    json.dumps(examples) if examples else None,
                    json.dumps(related_concepts) if related_concepts else None,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
        
        # Store in knowledge vector store
        concept_text = f"Concept: {concept_name}\nDefinition: {definition}"
        if examples:
            concept_text += f"\nExamples: {'; '.join(examples)}"
        
        # Generate embedding
        embedding = self.embedding_model.encode([concept_text])['dense_vecs'][0].tolist()
        concept_id = str(uuid.uuid4())
        
        metadata = {
            "concept_name": concept_name,
            "legal_domain": legal_domain,
            "related_concepts": json.dumps(related_concepts or [])
        }
        
        # Add to knowledge collection
        self.knowledge_collection.add(
            embeddings=[embedding],
            documents=[concept_text],
            metadatas=[metadata],
            ids=[concept_id]
        )
    
    def search_legal_concepts(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant legal concepts."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])['dense_vecs'][0].tolist()
        
        # Search in knowledge collection
        results = self.knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_user_interaction_history(
        self, 
        user_id: str, 
        limit: int = 50,
        legal_domain: Optional[str] = None
    ) -> List[UserInteraction]:
        """Get user's interaction history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT timestamp, user_input, ai_response, legal_domain, case_type, 
                       jurisdiction, satisfaction_score, topics
                FROM interactions 
                WHERE user_id = ?
            """
            params = [user_id]
            
            if legal_domain:
                query += " AND legal_domain = ?"
                params.append(legal_domain)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            interactions = []
            for row in results:
                interactions.append(UserInteraction(
                    timestamp=datetime.fromisoformat(row[0]),
                    user_input=row[1],
                    ai_response=row[2],
                    legal_domain=row[3],
                    case_type=row[4],
                    jurisdiction=row[5],
                    satisfaction_score=row[6],
                    topics=json.loads(row[7]) if row[7] else None
                ))
            
            return interactions
    
    def get_memory_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics about memory usage."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            analytics = {}
            
            if user_id:
                # User-specific analytics
                cursor.execute("""
                    SELECT COUNT(*), AVG(satisfaction_score)
                    FROM interactions 
                    WHERE user_id = ?
                """, (user_id,))
                user_stats = cursor.fetchone()
                
                analytics["user_interactions"] = user_stats[0]
                analytics["user_avg_satisfaction"] = user_stats[1]
                
                # User's top domains
                cursor.execute("""
                    SELECT legal_domain, COUNT(*) as count
                    FROM interactions 
                    WHERE user_id = ? AND legal_domain IS NOT NULL
                    GROUP BY legal_domain
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id,))
                analytics["user_top_domains"] = dict(cursor.fetchall())
            else:
                # System-wide analytics
                cursor.execute("SELECT COUNT(*) FROM user_profiles")
                analytics["total_users"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM interactions")
                analytics["total_interactions"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM learned_concepts")
                analytics["total_concepts"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(satisfaction_score) FROM interactions WHERE satisfaction_score IS NOT NULL")
                analytics["avg_satisfaction"] = cursor.fetchone()[0]
            
            return analytics
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> None:
        """Clean up old interaction data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM interactions 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            conn.commit()
        
        # Note: Vector stores cleanup would require more complex operations
        # This is a simplified version
