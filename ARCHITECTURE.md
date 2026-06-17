# Architecture Overview

This document describes the architecture of the MongoDB RAG application (`rag-app`).

## What It Does

A **Retrieval-Augmented Generation (RAG)** application built for MongoDB's GenAI Developer Day. It answers questions about MongoDB documentation by retrieving relevant chunks from **MongoDB Atlas Vector Search** and generating answers with an **LLM** — grounded in retrieved context, not model memory alone.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients
        CLI["query.py / ingest_data.py"]
        API["api.py (FastAPI)"]
    end

    subgraph RAG_App["rag-app (Python)"]
        GEN["AnswerGenerator"]
        RET["VectorRetriever"]
        MEM["ChatMemory"]
        EMB["VoyageEmbeddings"]
        CHK["TextChunker"]
        PROC["DataProcessor"]
        IDX["IndexManager"]
        DB["MongoDBClient"]
    end

    subgraph External
        VOY["Voyage AI API"]
        LLM["LLM Proxy"]
    end

    subgraph Atlas["MongoDB Atlas"]
        KB[("knowledge_base\nchunks + embeddings")]
        CH[("chat_history\nsession messages")]
        VS["vector_index\n(cosine, 1024-dim)"]
    end

    CLI --> GEN
    API --> GEN
    CLI --> PROC
    PROC --> CHK --> EMB --> DB
    PROC --> IDX --> VS

    GEN --> RET --> EMB --> VOY
    RET --> KB
    GEN --> MEM --> CH
    GEN --> LLM
    DB --> KB
    DB --> CH
    KB --- VS
```

## Project Structure

```
rag-app/
├── api.py                 # REST API (FastAPI)
├── ingest_data.py         # One-time / periodic data load
├── query.py               # CLI query interface
├── config/settings.py     # All tunables + env vars
├── data/mongodb_docs.json # Source documents (you provide this)
└── src/
    ├── database/mongodb.py
    ├── embeddings/{chunker,voyage_embeddings}.py
    ├── rag/{retriever,generator}.py
    ├── memory/chat_history.py
    └── utils/{data_loader,index_manager}.py
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Vector DB | MongoDB Atlas (`$vectorSearch`) |
| Embeddings | Voyage AI `voyage-context-3` (1024-dim, contextualized) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| LLM | External proxy (`PROXY_ENDPOINT`) |
| API | FastAPI (`api.py`) |
| CLI | `ingest_data.py`, `query.py` |

## Flow 1: Data Ingestion

```mermaid
sequenceDiagram
    participant User
    participant ingest as ingest_data.py
    participant proc as DataProcessor
    participant chunk as TextChunker
    participant voyage as VoyageEmbeddings
    participant mongo as MongoDBClient
    participant idx as IndexManager
    participant atlas as Atlas knowledge_base

    User->>ingest: python ingest_data.py
    ingest->>proc: load_json_data(mongodb_docs.json)
    loop For each document
        proc->>chunk: split body (200 tokens, overlap 0)
        chunk-->>proc: chunks[]
        proc->>voyage: contextualized_embed(chunks, "document")
        voyage-->>proc: embeddings[] (1024-dim each)
        proc->>proc: one MongoDB doc per chunk
    end
    ingest->>mongo: delete_all_documents()
    ingest->>mongo: insert_documents(embedded_docs)
    ingest->>idx: create_basic_index()
    idx->>atlas: vectorSearch index on embedding field
    idx->>idx: poll until READY
```

Each chunk document preserves original metadata (`metadata.productName`, `metadata.contentType`, `updated`, etc.), replaces `body` with the chunk text, and adds a 1024-float `embedding` vector from Voyage.

Chunking uses tiktoken (GPT-4 encoder) with separators `["\n\n", "\n", " ", "", "#", "##", "###"]` so markdown-style docs split sensibly.

## Flow 2: Query / RAG Pipeline

```mermaid
sequenceDiagram
    participant User
    participant api as api.py / query.py
    participant gen as AnswerGenerator
    participant mem as ChatMemory
    participant ret as VectorRetriever
    participant voyage as VoyageEmbeddings
    participant atlas as Atlas $vectorSearch
    participant llm as LLM Proxy

    User->>api: "What are backup best practices?" (+ optional session_id)
    api->>gen: generate(query, session_id, use_rerank)

    alt use_rerank = true
        gen->>ret: search_with_rerank(query)
        ret->>voyage: embed query ("query" type)
        ret->>atlas: $vectorSearch (150 candidates → top 5)
        ret->>voyage: rerank(query, doc bodies)
    else use_rerank = false
        gen->>ret: search(query)
        ret->>voyage: embed query
        ret->>atlas: $vectorSearch (limit 5)
    end

    atlas-->>ret: top chunks + vectorSearchScore
    ret-->>gen: context documents

    gen->>gen: build prompt: context + question
    opt session_id provided
        gen->>mem: retrieve_history(session_id)
        mem-->>gen: prior user/assistant messages
    end

    gen->>llm: POST { task: "completion", data: messages }
    llm-->>gen: generated answer

    opt session_id provided
        gen->>mem: store user + assistant messages
    end

    gen-->>api: answer
    api-->>User: response
```

The system is **grounded**: if retrieval returns nothing useful, the model is instructed to say *"I DON'T KNOW"* rather than hallucinate.

## Vector Search Internals

```mermaid
flowchart LR
    Q["User query"] --> E["Voyage embed\n(input_type: query)"]
    E --> V["1024-dim queryVector"]
    V --> A["$vectorSearch aggregation"]
    A --> C["numCandidates: 150"]
    C --> L["limit: 5 results"]
    L --> P["$project: body, metadata, score"]
    P --> R["Retrieved chunks"]

    F["Optional filter_criteria"] -.-> A
```

| Setting | Value | Purpose |
|---------|-------|---------|
| `NUM_CANDIDATES` | 150 | ANN search pool size |
| `VECTOR_SEARCH_LIMIT` | 5 | Chunks passed to LLM |
| `RERANK_TOP_K` | 5 | After reranking |
| Similarity | cosine | Vector distance metric |
| Index name | `vector_index` | Atlas search index |

**Pre-filtering** (advanced): `IndexManager.create_index_with_filters()` adds filter fields (e.g. `metadata.productName`) so `VectorRetriever.search(filter_criteria={...})` can narrow results before similarity ranking.

## Module Responsibilities

```mermaid
mindmap
  root((rag-app))
    database
      MongoDBClient
      connection pooling
      vector index CRUD
      session index
    embeddings
      TextChunker
      VoyageEmbeddings
      contextualized embed
      rerank-2.5
    rag
      VectorRetriever
      AnswerGenerator
    memory
      ChatMemory
      per session_id
    utils
      DataProcessor
      IndexManager
    config
      settings singleton
      env validation
```

| Module | File | Role |
|--------|------|------|
| **Database** | `mongodb.py` | Connects to `mongodb_genai_devday_rag`; manages `knowledge_base` + `chat_history` |
| **Embeddings** | `voyage_embeddings.py` | `contextualized_embed` for docs/queries; `rerank` for relevance boost |
| **Embeddings** | `chunker.py` | Splits long docs into ~200-token chunks |
| **RAG** | `retriever.py` | Builds `$vectorSearch` pipeline, optional rerank |
| **RAG** | `generator.py` | Orchestrates retrieve → prompt → LLM → memory |
| **Memory** | `chat_history.py` | Stores `{session_id, role, content, timestamp}` in MongoDB |
| **Utils** | `data_loader.py` | JSON load + chunk + embed pipeline |
| **Utils** | `index_manager.py` | Creates Atlas vector index, waits for READY |
| **Config** | `settings.py` | Central config from `.env` |

## MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `knowledge_base` | Document chunks + embeddings |
| `chat_history` | Per-session conversation messages |

## API Surface (`api.py`)

On startup, the API wires all components once: `MongoDBClient` → `VoyageEmbeddings` → `VectorRetriever` → `ChatMemory` → `AnswerGenerator`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | MongoDB + embeddings health |
| `/stats` | GET | Doc count, model, chunk size |
| `/query` | POST | Full RAG answer |
| `/search` | GET | Raw vector search (no LLM) |
| `/history/{session_id}` | GET | Fetch chat history |
| `/history/{session_id}` | DELETE | Clear session |

**Example query request:**

```json
{
  "query": "What are best practices for MongoDB backups?",
  "session_id": "user123",
  "use_rerank": false
}
```

## Configuration & Dependencies

**Required env vars** (`.env`):

- `MONGODB_URI` — Atlas connection string
- `PROXY_ENDPOINT` — LLM completion proxy URL
- `VOYAGE_API_KEY` — or workshop `PASSKEY` via proxy

```mermaid
flowchart TB
    subgraph Required
        A["MongoDB Atlas\n(Vector Search enabled)"]
        V["Voyage AI\n(embed + rerank)"]
        L["LLM Proxy\n(completion API)"]
    end

    subgraph Optional
        UI["rag-app-ui\n(separate frontend)"]
    end

    RAG["rag-app"] --> A
    RAG --> V
    RAG --> L
    UI -.->|HTTP /query| RAG
```

## Design Choices

1. **Contextualized embeddings** — Voyage's `voyage-context-3` embeds chunks *in document context*, which tends to improve retrieval vs. naive per-chunk embedding.
2. **Two-stage retrieval** — Vector search casts a wide net (150 candidates); optional reranking (`rerank-2.5`) re-scores the top bodies for sharper relevance.
3. **MongoDB as dual store** — Same database holds vectors *and* chat memory; no separate vector DB or Redis needed.
4. **Modular CLI + API** — Same core classes power both `query.py` and `api.py`; ingestion is a separate offline job.
5. **Session memory** — History is stored in MongoDB keyed by `session_id`, enabling multi-turn conversations.

## Typical Usage Lifecycle

```mermaid
flowchart TD
    A["1. Configure .env"] --> B["2. Place mongodb_docs.json in data/"]
    B --> C["3. python ingest_data.py"]
    C --> D{"Index READY?"}
    D -->|No| E["Wait / retry"]
    E --> D
    D -->|Yes| F["4. Query"]
    F --> G["CLI: python query.py ..."]
    F --> H["API: python api.py → POST /query"]
    F --> I["Optional: --session-id for memory"]
    F --> J["Optional: --rerank for quality"]
```
