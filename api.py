"""
FastAPI server for the RAG application.

This provides REST API endpoints to query the RAG system.
"""
import sys
import os
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings
from database import MongoDBClient
from embeddings import VoyageEmbeddings
from memory import ChatMemory
from rag import VectorRetriever, AnswerGenerator


# Initialize FastAPI app
app = FastAPI(
    title="MongoDB RAG API",
    description="REST API for querying MongoDB documentation using RAG",
    version="1.0.0"
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    query: str = Field(..., description="The question to ask", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation history")
    use_rerank: bool = Field(False, description="Whether to use reranking for better results")
    filter_criteria: Optional[Dict] = Field(None, description="Optional filter criteria for vector search")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are best practices for MongoDB backups?",
                "session_id": "user123",
                "use_rerank": False
            }
        }


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str = Field(..., description="The generated answer")
    session_id: Optional[str] = Field(None, description="Session ID if provided")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the context...",
                "session_id": "user123"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    mongodb: str
    embeddings: str


class SearchResult(BaseModel):
    """Individual search result."""
    body: str
    score: float
    metadata: Optional[Dict] = None


class SearchResponse(BaseModel):
    """Response for vector search."""
    query: str
    results: List[SearchResult]
    count: int


# Initialize components (done once at startup)
mongo_client: Optional[MongoDBClient] = None
embeddings: Optional[VoyageEmbeddings] = None
retriever: Optional[VectorRetriever] = None
chat_memory: Optional[ChatMemory] = None
generator: Optional[AnswerGenerator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize all components when the API starts."""
    global mongo_client, embeddings, retriever, chat_memory, generator
    
    try:
        # Validate settings
        settings.validate()
        
        # Initialize MongoDB client
        mongo_client = MongoDBClient()
        
        # Test connection
        mongo_client.ping()
        print("✓ MongoDB connected")
        
        # Initialize embeddings
        embeddings = VoyageEmbeddings()
        print("✓ Embeddings initialized")
        
        # Initialize retriever
        retriever = VectorRetriever(
            collection=mongo_client.get_collection(),
            embeddings=embeddings
        )
        print("✓ Retriever initialized")
        
        # Initialize chat memory
        mongo_client.create_session_index()
        chat_memory = ChatMemory(mongo_client.get_history_collection())
        print("✓ Chat memory initialized")
        
        # Initialize answer generator
        generator = AnswerGenerator(
            retriever=retriever,
            chat_memory=chat_memory
        )
        print("✓ Generator initialized")
        
        print("\n🚀 RAG API is ready!")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        raise


@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "MongoDB RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check MongoDB
        mongo_status = "healthy"
        try:
            mongo_client.ping()
        except:
            mongo_status = "unhealthy"
        
        # Check embeddings
        embeddings_status = "healthy" if embeddings else "unhealthy"
        
        overall = "healthy" if mongo_status == "healthy" and embeddings_status == "healthy" else "unhealthy"
        
        return {
            "status": overall,
            "mongodb": mongo_status,
            "embeddings": embeddings_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with a question.
    
    This endpoint:
    1. Embeds your query
    2. Searches for relevant documents in MongoDB
    3. Generates an answer using the LLM
    4. Optionally maintains conversation history
    """
    try:
        if not generator:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Generate answer
        answer = generator.generate(
            user_query=request.query,
            session_id=request.session_id,
            use_rerank=request.use_rerank
        )
        
        return QueryResponse(
            answer=answer,
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.get("/search", response_model=SearchResponse, tags=["RAG"])
async def vector_search(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(5, description="Number of results", ge=1, le=20),
    use_rerank: bool = Query(False, description="Use reranking")
):
    """
    Perform vector search without generating an answer.
    
    Returns raw search results with similarity scores.
    """
    try:
        if not retriever:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform search
        if use_rerank:
            results = retriever.search_with_rerank(
                user_query=query,
                rerank_top_k=limit
            )
        else:
            results = retriever.search(
                user_query=query,
                limit=limit
            )
        
        # Format results
        search_results = [
            SearchResult(
                body=r.get("body", ""),
                score=r.get("score", r.get("rerank_score", 0.0)),
                metadata=r.get("metadata")
            )
            for r in results
        ]
        
        return SearchResponse(
            query=query,
            results=search_results,
            count=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")


@app.delete("/history/{session_id}", tags=["Memory"])
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    try:
        if not chat_memory:
            raise HTTPException(status_code=503, detail="Chat memory not initialized")
        
        chat_memory.clear_history(session_id)
        
        return {
            "message": f"History cleared for session: {session_id}",
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


@app.get("/history/{session_id}", tags=["Memory"])
async def get_history(session_id: str):
    """Get conversation history for a session."""
    try:
        if not chat_memory:
            raise HTTPException(status_code=503, detail="Chat memory not initialized")
        
        history = chat_memory.retrieve_history(session_id)
        
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@app.get("/stats", tags=["General"])
async def get_stats():
    """Get statistics about the RAG system."""
    try:
        if not mongo_client:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        doc_count = mongo_client.count_documents()
        
        return {
            "documents": doc_count,
            "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
            "embedding_model": settings.EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "database": settings.DB_NAME,
            "collection": settings.COLLECTION_NAME
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the RAG API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"Starting RAG API on http://{args.host}:{args.port}")
    print(f"API Documentation: http://{args.host}:{args.port}/docs")
    
    start_server(host=args.host, port=args.port, reload=args.reload)

