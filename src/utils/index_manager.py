"""
Vector search index management utilities.
"""
from typing import Dict, List
from pymongo.collection import Collection

from config import settings
from database import create_vector_search_index, check_index_ready


class IndexManager:
    """Manage vector search indexes."""
    
    def __init__(self, collection: Collection):
        """
        Initialize index manager.
        
        Args:
            collection: MongoDB collection to manage indexes for
        """
        self.collection = collection
    
    def create_basic_index(self) -> bool:
        """
        Create a basic vector search index without filters.
        
        Returns:
            True if index is created and ready, False otherwise
        """
        model = {
            "name": settings.ATLAS_VECTOR_SEARCH_INDEX_NAME,
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": settings.EMBEDDING_DIMENSIONS,
                        "similarity": "cosine",
                    }
                ]
            },
        }
        
        create_vector_search_index(
            self.collection,
            settings.ATLAS_VECTOR_SEARCH_INDEX_NAME,
            model
        )
        
        return check_index_ready(
            self.collection,
            settings.ATLAS_VECTOR_SEARCH_INDEX_NAME
        )
    
    def create_index_with_filters(self, filter_fields: List[str]) -> bool:
        """
        Create a vector search index with filter fields.
        
        Args:
            filter_fields: List of fields to add as filters
            
        Returns:
            True if index is created and ready, False otherwise
        """
        fields = [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.EMBEDDING_DIMENSIONS,
                "similarity": "cosine"
            }
        ]
        
        # Add filter fields
        for field in filter_fields:
            fields.append({"type": "filter", "path": field})
        
        model = {
            "name": settings.ATLAS_VECTOR_SEARCH_INDEX_NAME,
            "type": "vectorSearch",
            "definition": {"fields": fields}
        }
        
        create_vector_search_index(
            self.collection,
            settings.ATLAS_VECTOR_SEARCH_INDEX_NAME,
            model
        )
        
        return check_index_ready(
            self.collection,
            settings.ATLAS_VECTOR_SEARCH_INDEX_NAME
        )

