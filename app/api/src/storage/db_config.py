import os
import logging
from typing import Optional
from urllib.parse import quote_plus
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env automatically when module is imported
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not available, using system environment variables only")

class PostgresConfig:
    """PostgreSQL database configuration"""
    
    @property
    def host(self) -> str:
        return os.getenv("POSTGRES_HOST", "localhost")
    
    @property
    def port(self) -> int:
        return int(os.getenv("POSTGRES_PORT", "5432"))
    
    @property
    def database(self) -> str:
        return os.getenv("POSTGRES_DB", "ila_system")
    
    @property
    def username(self) -> str:
        return os.getenv("POSTGRES_USER", "postgres")
    
    @property
    def password(self) -> str:
        return os.getenv("POSTGRES_PASSWORD", "")
    
    @property
    def ssl_mode(self) -> str:
        return os.getenv("POSTGRES_SSL_MODE", "prefer")
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string for psycopg2"""
        encoded_password = quote_plus(self.password) if self.password else ""
        if encoded_password:
            return f"postgresql://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
    
    @property
    def psycopg2_dsn(self) -> str:
        """Generate psycopg2 DSN connection string"""
        dsn_parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.database}",
            f"user={self.username}",
            f"sslmode={self.ssl_mode}"
        ]
        if self.password:
            dsn_parts.append(f"password={self.password}")
        return " ".join(dsn_parts)

class ChromaDBConfig:
    """ChromaDB configuration"""
    
    @property
    def host(self) -> str:
        return os.getenv("CHROMA_HOST", "localhost")
    
    @property
    def port(self) -> int:
        return int(os.getenv("CHROMA_PORT", "8000"))
    
    @property
    def legal_cases_collection(self) -> str:
        return os.getenv("CHROMA_LEGAL_CASES_COLLECTION", "legal_cases")
    
    @property
    def legislation_collection(self) -> str:
        return os.getenv("CHROMA_LEGISLATION_COLLECTION", "legislation")
    
    @property
    def persist_directory(self) -> Optional[str]:
        return os.getenv("CHROMA_PERSIST_DIR", "./vector_db")
    
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

    @property
    def collections(self) -> dict:
        """Get collection names"""
        return {
            "legal_cases": self.legal_cases_collection,
            "legislation": self.legislation_collection
        }

class DatabaseConfig:
    """Combined database configuration"""
    
    def __init__(self):
        self.postgres = PostgresConfig()
        self.chroma = ChromaDBConfig()
        logger.info("Database configuration initialized")
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.postgres.database:
            raise ValueError("PostgreSQL database name is required")
        if not self.chroma.legal_cases_collection or not self.chroma.legislation_collection:
            raise ValueError("ChromaDB collection names are required")
        logger.info("Database configuration validation passed")
        return True
    
    def get_postgres_connection(self):
        """Get a psycopg2 connection using the configuration"""
        try:
            logger.info(f"Attempting PostgreSQL connection to {self.postgres.host}:{self.postgres.port}/{self.postgres.database}")
            
            # Use the psycopg2_dsn property for connection
            conn = psycopg2.connect(self.postgres.psycopg2_dsn)
            logger.info("Successfully connected to PostgreSQL")
            return conn
        except ImportError:
            logger.error("psycopg2 is required for PostgreSQL connections. Install with: pip install psycopg2-binary")
            raise ImportError("psycopg2 is required for PostgreSQL connections. Install with: pip install psycopg2-binary")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

# Simple global instance
db_config = DatabaseConfig()

def main():
    """Example usage of database configuration"""
    print("=== Database Configuration Example ===\n")
    
    # No need to manually load - already loaded at import time
    config = DatabaseConfig()
    
    print("PostgreSQL Configuration:")
    print(f"  Host: {config.postgres.host}")
    print(f"  Port: {config.postgres.port}")
    print(f"  Database: {config.postgres.database}")
    print(f"  Username: {config.postgres.username}")
    print(f"  Password: {'***SET***' if config.postgres.password else 'NOT_SET'}")
    print(f"  SSL Mode: {config.postgres.ssl_mode}")
    
    print("\nChromaDB Configuration:")
    print(f"  Host: {config.chroma.host}")
    print(f"  Port: {config.chroma.port}")
    print(f"  Persist Directory: {config.chroma.persist_directory}")
    print(f"  Collections: {config.chroma.collections}")
    print(f"  Client Settings: {config.chroma.client_settings}")
    
    print("\nValidation:")
    try:
        is_valid = config.validate()
        print(f"  Configuration is valid: {is_valid}")
    except ValueError as e:
        print(f"  Configuration error: {e}")
    
    print("\n=== Database Connection Example ===")
    try:
        conn = config.get_postgres_connection()
        print("✓ Successfully connected to PostgreSQL!")
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"  PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        print("✓ Connection closed successfully")
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == "__main__":
    main()

