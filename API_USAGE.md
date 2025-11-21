# RAG API Usage Guide

Your RAG application is now available as a REST API!

## Quick Start

### 1. Install New Dependencies

```bash
cd /Users/alface/Repos/Tutorials/AI/MongoDB/rag-app
source venv/bin/activate
pip install fastapi uvicorn[standard]
```

### 2. Start the API Server

```bash
# Development mode (with auto-reload)
python api.py --reload

# Production mode
python api.py

# Custom host and port
python api.py --host 0.0.0.0 --port 8080
```

The API will be available at: **http://localhost:8000**

### 3. View Interactive API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 🏠 General Endpoints

#### `GET /`
Root endpoint with API information.

```bash
curl http://localhost:8000/
```

#### `GET /health`
Health check endpoint.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "mongodb": "healthy",
  "embeddings": "healthy"
}
```

#### `GET /stats`
Get RAG system statistics.

```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "documents": 101,
  "embedding_dimensions": 1024,
  "embedding_model": "voyage-context-3",
  "chunk_size": 200,
  "database": "mongodb_genai_devday_rag",
  "collection": "knowledge_base"
}
```

---

### 🤖 RAG Endpoints

#### `POST /query`
Query the RAG system with a question.

**Simple Query:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are MongoDB best practices for backups?"
  }'
```

**With Conversation History:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about MongoDB alerts",
    "session_id": "user123"
  }'
```

**With Reranking:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to resolve alerts?",
    "use_rerank": true
  }'
```

**With Filter Criteria:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Best practices for MongoDB",
    "filter_criteria": {
      "metadata.productName": "MongoDB Atlas"
    }
  }'
```

Response:
```json
{
  "answer": "Based on the context provided, here are some best practices...",
  "session_id": "user123"
}
```

#### `GET /search`
Perform vector search without generating an answer.

```bash
curl "http://localhost:8000/search?query=MongoDB%20backups&limit=3"
```

With reranking:
```bash
curl "http://localhost:8000/search?query=MongoDB%20backups&limit=5&use_rerank=true"
```

Response:
```json
{
  "query": "MongoDB backups",
  "results": [
    {
      "body": "Document content...",
      "score": 0.85,
      "metadata": {...}
    }
  ],
  "count": 3
}
```

---

### 💬 Memory Endpoints

#### `GET /history/{session_id}`
Get conversation history for a session.

```bash
curl http://localhost:8000/history/user123
```

Response:
```json
{
  "session_id": "user123",
  "messages": [
    {"role": "user", "content": "Tell me about alerts"},
    {"role": "assistant", "content": "MongoDB alerts..."}
  ],
  "count": 2
}
```

#### `DELETE /history/{session_id}`
Clear conversation history for a session.

```bash
curl -X DELETE http://localhost:8000/history/user123
```

Response:
```json
{
  "message": "History cleared for session: user123",
  "session_id": "user123"
}
```

---

## Client Examples

### JavaScript/Node.js

```javascript
// Simple query
async function queryRAG(question) {
  const response = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: question,
      session_id: 'user-session-1',
      use_rerank: false
    })
  });
  
  const data = await response.json();
  console.log('Answer:', data.answer);
  return data;
}

// Usage
queryRAG('What are MongoDB best practices?');
```

### Python

```python
import requests

def query_rag(question, session_id=None):
    """Query the RAG API."""
    url = "http://localhost:8000/query"
    payload = {
        "query": question,
        "session_id": session_id,
        "use_rerank": False
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.json()
    return data["answer"]

# Usage
answer = query_rag("What are MongoDB best practices?", session_id="user1")
print(answer)
```

### cURL

```bash
#!/bin/bash

# Function to query RAG
query_rag() {
  local question="$1"
  local session_id="${2:-}"
  
  local data="{\"query\": \"$question\""
  
  if [ -n "$session_id" ]; then
    data="$data, \"session_id\": \"$session_id\""
  fi
  
  data="$data}"
  
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d "$data" \
    | jq -r '.answer'
}

# Usage
query_rag "What are MongoDB best practices?" "user1"
```

### React Frontend

```jsx
import { useState } from 'react';

function RAGChat() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const sessionId = 'user-' + Date.now();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          session_id: sessionId,
          use_rerank: true
        })
      });
      
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      console.error('Error:', error);
      setAnswer('Error getting answer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about MongoDB..."
        />
        <button disabled={loading}>
          {loading ? 'Loading...' : 'Ask'}
        </button>
      </form>
      
      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}
```

---

## API Request/Response Models

### QueryRequest

```json
{
  "query": "string (required)",
  "session_id": "string (optional)",
  "use_rerank": "boolean (optional, default: false)",
  "filter_criteria": "object (optional)"
}
```

### QueryResponse

```json
{
  "answer": "string",
  "session_id": "string (optional)"
}
```

---

## Error Handling

All errors return HTTP status codes with JSON error messages:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid parameters)
- `500` - Internal Server Error
- `503` - Service Unavailable (initialization failed)

---

## CORS Configuration

The API allows requests from any origin (`*`) for development.

**For production**, update `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t rag-api .
docker run -p 8000:8000 --env-file .env rag-api
```

### Using Gunicorn (Production)

```bash
pip install gunicorn

# Run with multiple workers
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## Testing

### Test API Health

```bash
curl http://localhost:8000/health
```

### Test Query Endpoint

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test question?"}'
```

### Load Testing

```bash
# Install Apache Bench
brew install httpd  # macOS

# Test 100 requests
ab -n 100 -c 10 -p query.json -T application/json http://localhost:8000/query
```

---

## Monitoring

View logs:
```bash
# The API logs requests automatically
# Check console output for:
# - Request logs
# - Error messages
# - MongoDB connection status
```

---

## Next Steps

1. ✅ Start the API server
2. ✅ Test with curl or Swagger UI
3. 🔨 Build your frontend
4. 🚀 Deploy to production

For more details, see the interactive documentation at http://localhost:8000/docs

