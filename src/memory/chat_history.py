"""
Chat history management module.
"""
from datetime import datetime
from typing import List, Dict
from pymongo.collection import Collection


class ChatMemory:
    """Chat memory manager for storing and retrieving conversation history."""
    
    def __init__(self, collection: Collection):
        """
        Initialize chat memory with a MongoDB collection.
        
        Args:
            collection: MongoDB collection for storing chat history
        """
        self.collection = collection
    
    def store_message(self, session_id: str, role: str, content: str) -> None:
        """
        Store a chat message in MongoDB.
        
        Args:
            session_id: Session ID of the message
            role: Role for the message (system, user, or assistant)
            content: Content of the message
        """
        message = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
        }
        self.collection.insert_one(message)
    
    def retrieve_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Retrieve chat message history for a particular session.
        
        Args:
            session_id: Session ID to retrieve chat message history for
            
        Returns:
            List of chat messages in the format [{"role": str, "content": str}, ...]
        """
        cursor = self.collection.find(
            {"session_id": session_id}
        ).sort("timestamp", 1)
        
        if cursor:
            messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in cursor
            ]
        else:
            messages = []
        
        return messages
    
    def clear_history(self, session_id: str) -> None:
        """
        Clear chat history for a session.
        
        Args:
            session_id: Session ID to clear history for
        """
        self.collection.delete_many({"session_id": session_id})

