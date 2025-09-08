import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

@dataclass
class PostgresConfig:
    """PostgreSQL database configuration"""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "ila_system")
    username: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    
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

@dataclass
class ChromaDBConfig:
    """ChromaDB configuration"""
    host: str = os.getenv("CHROMA_HOST", "localhost")
    port: int = int(os.getenv("CHROMA_PORT", "8000"))
    legal_cases_collection: str = os.getenv("CHROMA_LEGAL_CASES_COLLECTION", "legal_cases")
    legislation_collection: str = os.getenv("CHROMA_LEGISLATION_COLLECTION", "legislation")
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

    @property
    def collections(self) -> dict:
        """Get collection names"""
        return {
            "legal_cases": self.legal_cases_collection,
            "legislation": self.legislation_collection
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

# example usage, comment out when not needed
def main():
    """Example usage of database configuration"""
    print("=== Database Configuration Example ===\n")
    
    # Create configuration instance
    config = DatabaseConfig()
    
    print("PostgreSQL Configuration:")
    print(f"  Host: {config.postgres.host}")
    print(f"  Port: {config.postgres.port}")
    print(f"  Database: {config.postgres.database}")
    print(f"  Username: {config.postgres.username}")
    print(f"  Connection String: {config.postgres.connection_string}")
    print(f"  Psycopg2 DSN: {config.postgres.psycopg2_dsn}")
    
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
    
    print("\n=== Custom Configuration Example ===")
    
    # Create custom configuration
    custom_postgres = PostgresConfig(
        host="my-postgres-server.com",
        port=5433,
        database="my_legal_db",
        username="legal_user",
        password="secure_password"
    )
    
    custom_chroma = ChromaDBConfig(
        host="my-chroma-server.com",
        port=8001,
        legal_cases_collection="custom_cases",
        legislation_collection="custom_legislation"
    )
    
    custom_config = DatabaseConfig(
        postgres=custom_postgres,
        chroma=custom_chroma
    )
    
    print(f"Custom PostgreSQL connection: {custom_config.postgres.connection_string}")
    print(f"Custom ChromaDB settings: {custom_config.chroma.client_settings}")

if __name__ == "__main__":
    main()

