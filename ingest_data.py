"""
Data ingestion script for processing and loading documents into MongoDB.

This script:
1. Loads documents from a JSON file
2. Chunks the documents into smaller pieces
3. Generates embeddings for each chunk
4. Stores the embedded chunks in MongoDB
5. Creates a vector search index
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings
from database import MongoDBClient
from embeddings import TextChunker, VoyageEmbeddings
from utils import DataProcessor, IndexManager


def main():
    """Main data ingestion workflow."""
    # Validate settings
    print("Validating configuration...")
    settings.validate()
    
    # Initialize MongoDB client
    print("Connecting to MongoDB...")
    mongo_client = MongoDBClient()
    
    # Test connection
    ping_result = mongo_client.ping()
    print(f"MongoDB connection successful: {ping_result}")
    
    # Initialize embeddings and chunker
    print("Initializing embeddings and chunker...")
    embeddings = VoyageEmbeddings()
    chunker = TextChunker()
    
    # Initialize data processor
    processor = DataProcessor(chunker, embeddings)
    
    # Load data
    data_file = os.path.join(os.path.dirname(__file__), "data", "mongodb_docs.json")
    if not os.path.exists(data_file):
        print(f"Error: Data file not found at {data_file}")
        print("Please ensure mongodb_docs.json is in the data/ directory")
        return
    
    print(f"Loading data from {data_file}...")
    docs = processor.load_json_data(data_file)
    print(f"Loaded {len(docs)} documents")
    
    # Process documents (chunk and embed)
    embedded_docs = processor.process_documents(docs, text_field="body")
    
    # Clear existing data
    print("Clearing existing documents from collection...")
    mongo_client.delete_all_documents()
    
    # Insert embedded documents
    print("Inserting embedded documents into MongoDB...")
    mongo_client.insert_documents(embedded_docs)
    
    doc_count = mongo_client.count_documents()
    print(f"Successfully ingested {doc_count} documents into MongoDB")
    
    # Create vector search index
    print("\nCreating vector search index...")
    index_manager = IndexManager(mongo_client.get_collection())
    success = index_manager.create_basic_index()
    
    if success:
        print("✓ Vector search index created successfully!")
    else:
        print("✗ Failed to create vector search index")
        return
    
    print("\n" + "="*50)
    print("Data ingestion completed successfully!")
    print("="*50)


if __name__ == "__main__":
    main()

