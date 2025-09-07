import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

@dataclass
class PostgresConfig:
    """PostgreSQL database configuration"""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "legal_assistant")
    username: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    ssl_mode: str = os.getenv("POSTGRES_SSL_MODE", "prefer")
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        encoded_password = quote_plus(self.password) if self.password else ""
        if encoded_password:
            return f"postgresql://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
    
    @property
    def async_connection_string(self) -> str:
        """Generate async PostgreSQL connection string"""
        return self.connection_string.replace("postgresql://", "postgresql+asyncpg://")

@dataclass
class ChromaDBConfig:
    """ChromaDB configuration"""
    host: str = os.getenv("CHROMA_HOST", "localhost")
    port: int = int(os.getenv("CHROMA_PORT", "8000"))
    collection_name: str = os.getenv("CHROMA_COLLECTION", "legal_documents")
    persist_directory: Optional[str] = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    @property
    def client_settings(self) -> dict:
        """Get ChromaDB client settings"""
        if self.host == "localhost" and self.persist_directory:
            # Local persistent storage
            return {"persist_directory": self.persist_directory}
        else:
            # Remote ChromaDB server
            return {
                "host": self.host,
                "port": self.port
            }

@dataclass
class DatabaseConfig:
    """Combined database configuration"""
    postgres: PostgresConfig = PostgresConfig()
    chroma: ChromaDBConfig = ChromaDBConfig()
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.postgres.database:
            raise ValueError("PostgreSQL database name is required")
        if not self.chroma.collection_name:
            raise ValueError("ChromaDB collection name is required")
        return True

# Global configuration instance
db_config = DatabaseConfig()