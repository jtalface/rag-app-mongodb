"""
Voyage AI embeddings and reranking module.
"""
import voyageai
from typing import List, Union

from config import settings


class VoyageEmbeddings:
    """Voyage AI embeddings client."""
    
    def __init__(self):
        """Initialize Voyage AI client."""
        self.client = voyageai.Client()
    
    def get_embeddings(
        self, 
        content: List[str], 
        input_type: str
    ) -> Union[List[float], List[List[float]]]:
        """
        Get contextualized embeddings for each chunk.
        
        Args:
            content: List of chunked texts or the user query as a list
            input_type: Type of input, either "document" or "query"
            
        Returns:
            Contextualized embeddings
        """
        embds_obj = self.client.contextualized_embed(
            inputs=[content],
            model=settings.EMBEDDING_MODEL,
            input_type=input_type
        )
        
        # If input_type is "document", there is a single result with multiple embeddings
        if input_type == "document":
            embeddings = [emb for r in embds_obj.results for emb in r.embeddings]
        # If input_type is "query", there is a single result with a single embedding
        elif input_type == "query":
            embeddings = embds_obj.results[0].embeddings[0]
        else:
            raise ValueError(f"Invalid input_type: {input_type}")
        
        return embeddings
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = None
    ) -> List:
        """
        Rerank documents using Voyage AI reranker.
        
        Args:
            query: User query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Reranked documents
        """
        if top_k is None:
            top_k = settings.RERANK_TOP_K
            
        reranked = self.client.rerank(
            query=query,
            documents=documents,
            model=settings.RERANK_MODEL,
            top_k=top_k
        )
        return reranked.results

