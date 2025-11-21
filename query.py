"""
Query script for interacting with the RAG application.

This script provides a command-line interface for querying the RAG system.
"""
import sys
import os
import argparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings
from database import MongoDBClient
from embeddings import VoyageEmbeddings
from memory import ChatMemory
from rag import VectorRetriever, AnswerGenerator


def main():
    """Main query workflow."""
    parser = argparse.ArgumentParser(
        description="Query the MongoDB RAG application"
    )
    parser.add_argument(
        "query",
        type=str,
        help="Your question or query"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Session ID for conversation history (optional)"
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Use reranking for better results"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Disable conversation history even if session-id is provided"
    )
    
    args = parser.parse_args()
    
    # Validate settings
    settings.validate()
    
    # Initialize MongoDB client
    mongo_client = MongoDBClient()
    
    # Initialize embeddings
    embeddings = VoyageEmbeddings()
    
    # Initialize retriever
    retriever = VectorRetriever(
        collection=mongo_client.get_collection(),
        embeddings=embeddings
    )
    
    # Initialize chat memory if session ID provided and history not disabled
    chat_memory = None
    if args.session_id and not args.no_history:
        # Create index on session_id if not exists
        mongo_client.create_session_index()
        chat_memory = ChatMemory(mongo_client.get_history_collection())
    
    # Initialize answer generator
    generator = AnswerGenerator(
        retriever=retriever,
        chat_memory=chat_memory
    )
    
    # Generate answer
    print(f"\nQuery: {args.query}\n")
    print("Generating answer...\n")
    
    answer = generator.generate(
        user_query=args.query,
        session_id=args.session_id,
        use_rerank=args.rerank
    )
    
    print("Answer:")
    print("-" * 50)
    print(answer)
    print("-" * 50)


if __name__ == "__main__":
    main()

