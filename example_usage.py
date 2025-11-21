"""
Example usage of the RAG application as a Python library.

This demonstrates how to use the RAG components programmatically
rather than through command-line scripts.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings
from database import MongoDBClient
from embeddings import VoyageEmbeddings
from memory import ChatMemory
from rag import VectorRetriever, AnswerGenerator


def example_simple_query():
    """Example: Simple query without conversation history."""
    print("=" * 60)
    print("Example 1: Simple Query")
    print("=" * 60)
    
    # Initialize components
    mongo_client = MongoDBClient()
    embeddings = VoyageEmbeddings()
    retriever = VectorRetriever(
        collection=mongo_client.get_collection(),
        embeddings=embeddings
    )
    generator = AnswerGenerator(retriever=retriever)
    
    # Generate answer
    query = "What are some best practices for data backups in MongoDB?"
    print(f"\nQuery: {query}\n")
    
    answer = generator.generate(user_query=query, use_rerank=False)
    print(f"Answer:\n{answer}\n")


def example_conversation():
    """Example: Multi-turn conversation with memory."""
    print("=" * 60)
    print("Example 2: Conversation with Memory")
    print("=" * 60)
    
    # Initialize components with memory
    mongo_client = MongoDBClient()
    embeddings = VoyageEmbeddings()
    retriever = VectorRetriever(
        collection=mongo_client.get_collection(),
        embeddings=embeddings
    )
    
    # Create session index
    mongo_client.create_session_index()
    chat_memory = ChatMemory(mongo_client.get_history_collection())
    
    generator = AnswerGenerator(
        retriever=retriever,
        chat_memory=chat_memory
    )
    
    session_id = "example_session_123"
    
    # First query
    query1 = "What are some best practices for data backups in MongoDB?"
    print(f"\nQuery 1: {query1}\n")
    
    answer1 = generator.generate(
        user_query=query1,
        session_id=session_id,
        use_rerank=False
    )
    print(f"Answer 1:\n{answer1}\n")
    
    # Follow-up query (tests conversation memory)
    query2 = "What did I just ask you?"
    print(f"\nQuery 2: {query2}\n")
    
    answer2 = generator.generate(
        user_query=query2,
        session_id=session_id,
        use_rerank=False
    )
    print(f"Answer 2:\n{answer2}\n")
    
    # Clean up (optional)
    # chat_memory.clear_history(session_id)


def example_with_reranking():
    """Example: Query with reranking for better results."""
    print("=" * 60)
    print("Example 3: Query with Reranking")
    print("=" * 60)
    
    # Initialize components
    mongo_client = MongoDBClient()
    embeddings = VoyageEmbeddings()
    retriever = VectorRetriever(
        collection=mongo_client.get_collection(),
        embeddings=embeddings
    )
    generator = AnswerGenerator(retriever=retriever)
    
    # Generate answer with reranking
    query = "How to resolve alerts in MongoDB?"
    print(f"\nQuery: {query}\n")
    
    answer = generator.generate(user_query=query, use_rerank=True)
    print(f"Answer:\n{answer}\n")


def example_filtered_search():
    """Example: Vector search with pre-filtering."""
    print("=" * 60)
    print("Example 4: Filtered Vector Search")
    print("=" * 60)
    
    # Initialize components
    mongo_client = MongoDBClient()
    embeddings = VoyageEmbeddings()
    retriever = VectorRetriever(
        collection=mongo_client.get_collection(),
        embeddings=embeddings
    )
    
    # Search with filter
    query = "What are some best practices for data backups?"
    filter_criteria = {"metadata.productName": "MongoDB Atlas"}
    
    print(f"\nQuery: {query}")
    print(f"Filter: {filter_criteria}\n")
    
    results = retriever.search(
        user_query=query,
        filter_criteria=filter_criteria
    )
    
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.get('score', 'N/A'):.4f}")
        print(f"   Product: {result.get('metadata', {}).get('productName', 'N/A')}")
        print(f"   Preview: {result.get('body', '')[:100]}...\n")


def main():
    """Run all examples."""
    try:
        # Validate configuration
        settings.validate()
        
        # Run examples
        example_simple_query()
        print("\n" + "=" * 60 + "\n")
        
        example_conversation()
        print("\n" + "=" * 60 + "\n")
        
        example_with_reranking()
        print("\n" + "=" * 60 + "\n")
        
        example_filtered_search()
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with correct credentials")
        print("2. Run ingest_data.py to load documents")
        print("3. Installed all requirements (pip install -r requirements.txt)")


if __name__ == "__main__":
    main()

