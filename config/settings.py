"""
Configuration settings for the RAG application.
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    MONGODB_URI: str = os.environ.get("MONGODB_URI", "")
    DB_NAME: str = "mongodb_genai_devday_rag"
    COLLECTION_NAME: str = "knowledge_base"
    HISTORY_COLLECTION_NAME: str = "chat_history"
    ATLAS_VECTOR_SEARCH_INDEX_NAME: str = "vector_index"
    
    # AI Model Configuration
    PROXY_ENDPOINT: str = os.environ.get("PROXY_ENDPOINT", "")
    PASSKEY: Optional[str] = os.environ.get("PASSKEY")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "voyage-context-3"
    EMBEDDING_DIMENSIONS: int = 1024
    RERANK_MODEL: str = "rerank-2.5"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 0
    SEPARATORS: list = ["\n\n", "\n", " ", "", "#", "##", "###"]
    
    # Vector Search Configuration
    NUM_CANDIDATES: int = 150
    VECTOR_SEARCH_LIMIT: int = 5
    RERANK_TOP_K: int = 5
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required settings are present."""
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is required")


# Create a singleton instance
settings = Settings()


