"""
MongoDB connection and operations module.
"""
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Dict, List
import time

from config import settings


class MongoDBClient:
    """MongoDB client for handling database operations."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.DB_NAME]
        self.collection = self.db[settings.COLLECTION_NAME]
        self.history_collection = self.db[settings.HISTORY_COLLECTION_NAME]
        
    def ping(self) -> Dict:
        """Test connection to MongoDB."""
        return self.client.admin.command("ping")
    
    def insert_documents(self, documents: List[Dict]) -> None:
        """
        Bulk insert documents into the collection.
        
        Args:
            documents: List of documents to insert
        """
        self.collection.insert_many(documents)
        
    def delete_all_documents(self) -> None:
        """Delete all documents from the collection."""
        self.collection.delete_many({})
        
    def count_documents(self) -> int:
        """Count documents in the collection."""
        return self.collection.count_documents({})
    
    def create_session_index(self) -> str:
        """Create index on session_id for history collection."""
        return self.history_collection.create_index("session_id")
    
    def get_collection(self) -> Collection:
        """Get the main collection."""
        return self.collection
    
    def get_history_collection(self) -> Collection:
        """Get the history collection."""
        return self.history_collection


def create_vector_search_index(
    collection: Collection, 
    index_name: str, 
    index_definition: Dict
) -> None:
    """
    Create a vector search index on the collection.
    
    Args:
        collection: MongoDB collection
        index_name: Name of the index
        index_definition: Index definition dictionary
    """
    print(f"Creating the {index_name} index")
    
    # Check if index already exists
    existing_indexes = list(collection.list_search_indexes())
    index_exists = any(idx.get('name') == index_name for idx in existing_indexes)
    
    if index_exists:
        print(f"{index_name} index already exists, recreating...")
        print(f"Dropping {index_name} index")
        collection.drop_search_index(index_name)
        
        # Wait for deletion to complete
        while any(idx.get('name') == index_name for idx in list(collection.list_search_indexes())):
            time.sleep(1)
        
        print(f"{index_name} index deletion complete")
        print(f"Creating new {index_name} index")
    
    # Create the index
    collection.create_search_index(index_definition)
    print(f"Successfully {'recreated' if index_exists else 'created'} the {index_name} index")


def check_index_ready(collection: Collection, index_name: str) -> bool:
    """
    Check if the vector search index is ready.
    
    Args:
        collection: MongoDB collection
        index_name: Name of the index to check
        
    Returns:
        bool: True if index is ready, False otherwise
    """
    # Wait for index to be ready
    max_attempts = 60
    attempts = 0
    
    while attempts < max_attempts:
        indexes = list(collection.list_search_indexes())
        for idx in indexes:
            if idx.get('name') == index_name:
                status = idx.get('status')
                if status == 'READY':
                    print(f"{index_name} index status: {status}")
                    print(f"{index_name} index definition: {idx.get('latestDefinition')}")
                    return True
                elif status in ['FAILED', 'DELETING']:
                    print(f"{index_name} index status: {status}")
                    return False
        
        time.sleep(2)
        attempts += 1
    
    print(f"Timeout waiting for {index_name} index to be ready")
    return False

