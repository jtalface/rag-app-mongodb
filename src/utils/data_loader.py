"""
Data loading and processing utilities.
"""
import json
from typing import List, Dict
from tqdm import tqdm

from embeddings import TextChunker, VoyageEmbeddings


class DataProcessor:
    """Process and embed documents for ingestion."""
    
    def __init__(self, chunker: TextChunker, embeddings: VoyageEmbeddings):
        """
        Initialize data processor.
        
        Args:
            chunker: TextChunker instance for document chunking
            embeddings: VoyageEmbeddings instance for generating embeddings
        """
        self.chunker = chunker
        self.embeddings = embeddings
    
    def load_json_data(self, file_path: str) -> List[Dict]:
        """
        Load JSON data from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of documents
        """
        with open(file_path, "r") as data_file:
            json_data = data_file.read()
        
        docs = json.loads(json_data)
        return docs
    
    def process_documents(
        self, 
        docs: List[Dict], 
        text_field: str = "body"
    ) -> List[Dict]:
        """
        Chunk and embed documents.
        
        Args:
            docs: List of documents to process
            text_field: Field containing text to chunk and embed
            
        Returns:
            List of processed documents with embeddings
        """
        embedded_docs = []
        
        print(f"Processing {len(docs)} documents...")
        for doc in tqdm(docs):
            # Chunk the document
            chunks = self.chunker.get_chunks(doc, text_field)
            
            # Get embeddings for all chunks
            chunk_embeddings = self.embeddings.get_embeddings(chunks, "document")
            
            # Create a new document for each chunk
            for chunk, embedding in zip(chunks, chunk_embeddings):
                chunk_doc = doc.copy()
                chunk_doc[text_field] = chunk
                chunk_doc["embedding"] = embedding
                embedded_docs.append(chunk_doc)
        
        print(f"Created {len(embedded_docs)} embedded chunks from {len(docs)} documents")
        return embedded_docs

