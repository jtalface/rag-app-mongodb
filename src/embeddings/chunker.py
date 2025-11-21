"""
Text chunking module using LangChain.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Dict, List

from config import settings


class TextChunker:
    """Text chunker for splitting documents into smaller chunks."""
    
    def __init__(self):
        """Initialize the text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4",
            separators=settings.SEPARATORS,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
    
    def get_chunks(self, doc: Dict, text_field: str) -> List[str]:
        """
        Chunk up a document.
        
        Args:
            doc: Parent document to generate chunks from
            text_field: Text field to chunk
            
        Returns:
            List of chunked text strings
        """
        text = doc[text_field]
        chunks = self.text_splitter.split_text(text)
        return chunks

