"""
Vector search retriever module.
"""
from typing import List, Dict
from pymongo.collection import Collection

from config import settings
from embeddings import VoyageEmbeddings


class VectorRetriever:
    """Vector search retriever for finding relevant documents."""
    
    def __init__(self, collection: Collection, embeddings: VoyageEmbeddings):
        """
        Initialize the retriever.
        
        Args:
            collection: MongoDB collection with vector search index
            embeddings: VoyageEmbeddings instance for generating query embeddings
        """
        self.collection = collection
        self.embeddings = embeddings
    
    def search(
        self, 
        user_query: str, 
        filter_criteria: Dict = None,
        num_candidates: int = None,
        limit: int = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a user query using vector search.
        
        Args:
            user_query: The user's query string
            filter_criteria: Optional filter criteria for pre-filtering
            num_candidates: Number of candidates to consider (default from settings)
            limit: Number of results to return (default from settings)
            
        Returns:
            List of matching documents
        """
        if num_candidates is None:
            num_candidates = settings.NUM_CANDIDATES
        if limit is None:
            limit = settings.VECTOR_SEARCH_LIMIT
        
        # Generate embedding for the user query
        query_embedding = self.embeddings.get_embeddings([user_query], "query")
        
        # Build vector search stage
        vector_search_stage = {
            "$vectorSearch": {
                "index": settings.ATLAS_VECTOR_SEARCH_INDEX_NAME,
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": num_candidates,
                "limit": limit
            }
        }
        
        # Add filter if provided
        if filter_criteria:
            vector_search_stage["$vectorSearch"]["filter"] = filter_criteria
        
        # Build aggregation pipeline
        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": 0,
                    "body": 1,
                    "metadata.productName": 1,
                    "metadata.contentType": 1,
                    "updated": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        # Execute the aggregation pipeline
        results = self.collection.aggregate(pipeline)
        return list(results)
    
    def search_with_rerank(
        self,
        user_query: str,
        filter_criteria: Dict = None,
        num_candidates: int = None,
        initial_limit: int = None,
        rerank_top_k: int = None
    ) -> List[Dict]:
        """
        Retrieve and rerank documents for a user query.
        
        Args:
            user_query: The user's query string
            filter_criteria: Optional filter criteria for pre-filtering
            num_candidates: Number of candidates to consider
            initial_limit: Initial number of results before reranking
            rerank_top_k: Number of top results after reranking
            
        Returns:
            List of reranked matching documents
        """
        if initial_limit is None:
            initial_limit = settings.VECTOR_SEARCH_LIMIT
        if rerank_top_k is None:
            rerank_top_k = settings.RERANK_TOP_K
        
        # Get initial results
        results = self.search(
            user_query=user_query,
            filter_criteria=filter_criteria,
            num_candidates=num_candidates,
            limit=initial_limit
        )
        
        # Extract document bodies for reranking
        documents = [d.get("body", "") for d in results]
        
        if not documents:
            return []
        
        # Rerank documents
        reranked = self.embeddings.rerank(
            query=user_query,
            documents=documents,
            top_k=rerank_top_k
        )
        
        # Return reranked results with original metadata
        reranked_results = []
        for rerank_result in reranked:
            # Get the original document by index
            original_doc = results[rerank_result.index]
            original_doc["rerank_score"] = rerank_result.relevance_score
            reranked_results.append(original_doc)
        
        return reranked_results

