"""
Answer generation module using LLM.
"""
import requests
from typing import List, Dict, Optional

from config import settings
from memory import ChatMemory
from rag.retriever import VectorRetriever


class AnswerGenerator:
    """RAG answer generator using vector retrieval and LLM."""
    
    def __init__(
        self, 
        retriever: VectorRetriever,
        chat_memory: Optional[ChatMemory] = None
    ):
        """
        Initialize the answer generator.
        
        Args:
            retriever: VectorRetriever instance for document retrieval
            chat_memory: Optional ChatMemory instance for conversation history
        """
        self.retriever = retriever
        self.chat_memory = chat_memory
    
    def create_prompt(self, user_query: str, use_rerank: bool = False) -> str:
        """
        Create a chat prompt with retrieved context.
        
        Args:
            user_query: The user's query string
            use_rerank: Whether to use reranking
            
        Returns:
            The chat prompt string
        """
        # Retrieve relevant documents
        if use_rerank:
            context_docs = self.retriever.search_with_rerank(user_query)
        else:
            context_docs = self.retriever.search(user_query)
        
        # Join documents into a single context string
        context = "\n\n".join([doc.get('body', '') for doc in context_docs])
        
        # Create prompt
        prompt = (
            f"Answer the question based only on the following context. "
            f"If the context is empty, say I DON'T KNOW\n\n"
            f"Context:\n{context}\n\n"
            f"Question:{user_query}"
        )
        return prompt
    
    def generate(
        self, 
        user_query: str, 
        session_id: Optional[str] = None,
        use_rerank: bool = False
    ) -> str:
        """
        Generate an answer to the user query.
        
        Args:
            user_query: The user's query string
            session_id: Optional session ID for conversation history
            use_rerank: Whether to use reranking
            
        Returns:
            Generated answer string
        """
        messages = []
        
        # Create system prompt with retrieved context
        prompt = self.create_prompt(user_query, use_rerank=use_rerank)
        system_message = {"role": "user", "content": prompt}
        messages.append(system_message)
        
        # Add conversation history if available
        if session_id and self.chat_memory:
            message_history = self.chat_memory.retrieve_history(session_id)
            messages.extend(message_history)
        
        # Add user query
        user_message = {"role": "user", "content": user_query}
        messages.append(user_message)
        
        # Call LLM API
        response = requests.post(
            url=settings.PROXY_ENDPOINT,
            json={"task": "completion", "data": messages}
        )
        
        if response.status_code == 200:
            answer = response.json()["text"]
        else:
            answer = f"Error: {response.json().get('error', 'Unknown error')}"
        
        # Store conversation in memory if session ID provided
        if session_id and self.chat_memory:
            self.chat_memory.store_message(session_id, "user", user_query)
            self.chat_memory.store_message(session_id, "assistant", answer)
        
        return answer

