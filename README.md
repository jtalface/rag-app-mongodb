# MongoDB RAG Application

A production-ready Retrieval-Augmented Generation (RAG) application built with MongoDB Atlas Vector Search, Voyage AI embeddings, and conversational memory.

## Features

- **Vector Search**: Semantic search using MongoDB Atlas Vector Search
- **Contextualized Embeddings**: Advanced embeddings using Voyage AI's contextualized embedding model
- **Document Chunking**: Intelligent text splitting with LangChain
- **Reranking**: Optional result reranking for improved relevance
- **Conversation Memory**: Chat history storage and retrieval for context-aware conversations
- **Pre-filtering**: Support for metadata filtering in vector search
- **Modular Architecture**: Clean separation of concerns with organized modules

## Project Structure

```
rag-app/
├── src/
│   ├── database/          # MongoDB connection and operations
│   ├── embeddings/        # Text chunking and embedding generation
│   ├── rag/              # Vector retrieval and answer generation
│   ├── memory/           # Chat history management
│   ├── utils/            # Data processing and index management
│   └── config/           # Configuration settings
├── data/                 # Data files (add your mongodb_docs.json here)
├── ingest_data.py       # Data ingestion script
├── query.py             # Query interface script
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # This file
```

## Installation

### 1. Clone or Navigate to the Repository

```bash
cd /path/to/rag-app
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your:
- MongoDB Atlas connection string (`MONGODB_URI`)
- AI model proxy endpoint (`PROXY_ENDPOINT`)
- Passkey or API keys as needed

### 5. Add Your Data

Place your `mongodb_docs.json` file in the `data/` directory.

## Usage

### Data Ingestion

Process and load documents into MongoDB with vector embeddings:

```bash
python ingest_data.py
```

This script will:
1. Load documents from `data/mongodb_docs.json`
2. Chunk documents into smaller pieces
3. Generate contextualized embeddings for each chunk
4. Store embedded chunks in MongoDB
5. Create a vector search index

### Querying the RAG System

#### Basic Query

```bash
python query.py "What are some best practices for data backups in MongoDB?"
```

#### Query with Conversation History

Use a session ID to maintain conversation context:

```bash
python query.py "What are some best practices for data backups?" --session-id user123
python query.py "What did I just ask you?" --session-id user123
```

#### Query with Reranking

Enable reranking for improved result relevance:

```bash
python query.py "How to resolve alerts in MongoDB?" --rerank
```

#### Query Options

```bash
python query.py --help
```

Options:
- `query`: Your question (required)
- `--session-id`: Session ID for conversation history
- `--rerank`: Enable result reranking
- `--no-history`: Disable conversation history

## Module Overview

### Database (`src/database/`)
- **mongodb.py**: MongoDB client, connection management, and index operations
- Handles vector search index creation and verification

### Embeddings (`src/embeddings/`)
- **chunker.py**: Document chunking using LangChain's RecursiveCharacterTextSplitter
- **voyage_embeddings.py**: Voyage AI integration for embeddings and reranking

### RAG (`src/rag/`)
- **retriever.py**: Vector search with optional pre-filtering and reranking
- **generator.py**: Answer generation using retrieved context and LLM

### Memory (`src/memory/`)
- **chat_history.py**: Conversation history storage and retrieval in MongoDB

### Utils (`src/utils/`)
- **data_loader.py**: Document loading and processing pipeline
- **index_manager.py**: Vector search index configuration and management

### Config (`src/config/`)
- **settings.py**: Centralized configuration management

## Configuration

All settings can be customized in `src/config/settings.py`:

- **MongoDB**: Database and collection names
- **Embeddings**: Model selection, dimensions, chunking parameters
- **Vector Search**: Number of candidates, search limits
- **Reranking**: Top-k results after reranking

## Advanced Features

### Pre-filtering

The application supports metadata filtering in vector search. To add filter fields:

```python
from utils import IndexManager

index_manager = IndexManager(collection)
index_manager.create_index_with_filters(
    filter_fields=["metadata.productName", "metadata.contentType", "updated"]
)
```

Then query with filters:

```python
retriever.search(
    user_query="your query",
    filter_criteria={"metadata.productName": "MongoDB Atlas"}
)
```

### Conversation Memory

Chat history is automatically stored when you provide a `session_id`:

```python
generator.generate(
    user_query="your question",
    session_id="user123"
)
```

### Reranking

Enable reranking to improve result relevance:

```python
retriever.search_with_rerank(
    user_query="your query",
    rerank_top_k=5
)
```

## Requirements

- Python 3.8+
- MongoDB Atlas cluster with Vector Search enabled
- Voyage AI API key
- Access to LLM proxy endpoint (for answer generation)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `PROXY_ENDPOINT` | AI model proxy endpoint URL | Yes |
| `PASSKEY` | Workshop passkey (if applicable) | Optional |
| `VOYAGE_API_KEY` | Voyage AI API key | Optional* |

*Set automatically via proxy if using PASSKEY

## Troubleshooting

### Import Errors

If you encounter import errors, ensure the `src/` directory is in your Python path:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

### MongoDB Connection Issues

- Verify your connection string is correct
- Ensure your IP address is whitelisted in MongoDB Atlas
- Check that your database user has appropriate permissions

### Vector Search Index Not Ready

Wait a few moments for the index to build after creation. The scripts include automatic polling to check index readiness.

## Development

To extend the application:

1. Add new modules in the appropriate `src/` subdirectory
2. Update `__init__.py` files to export new classes/functions
3. Import from the package: `from module_name import ClassName`

## License

This project is provided as-is for educational and development purposes.

## Acknowledgments

- MongoDB Atlas for vector search capabilities
- Voyage AI for contextualized embeddings and reranking
- LangChain for text processing utilities

