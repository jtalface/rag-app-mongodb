# 🚀 RAG Application - REST API

Your RAG application is now a **REST API** that can be accessed from any frontend (React, Vue, Angular) or backend service (Node.js, Python, etc.)!

## ✨ What's New

### Files Created

1. **`api.py`** - FastAPI server with REST endpoints
2. **`API_USAGE.md`** - Comprehensive API documentation
3. **`start_api.sh`** - Easy start script

### API Endpoints

- `POST /query` - Ask questions (main endpoint)
- `GET /search` - Vector search without LLM
- `GET /health` - Health check
- `GET /stats` - System statistics
- `GET /history/{session_id}` - Get conversation history
- `DELETE /history/{session_id}` - Clear conversation history

---

## 🏃 Quick Start

### 1. Start the API Server

```bash
cd /Users/alface/Repos/Tutorials/AI/MongoDB/rag-app
./start_api.sh
```

Or manually:
```bash
source venv/bin/activate
python api.py
```

The API will be available at: **http://localhost:8000**

### 2. View Interactive Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs (try it out!)
- **ReDoc**: http://localhost:8000/redoc

### 3. Test with cURL

```bash
# Simple query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are MongoDB best practices?"}'

# With conversation memory
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about backups",
    "session_id": "user123"
  }'

# Check health
curl http://localhost:8000/health
```

---

## 🌐 Use from Frontend

### JavaScript/Fetch

```javascript
async function askQuestion(question) {
  const response = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: question,
      session_id: 'user-session-1',
      use_rerank: false
    })
  });
  
  const data = await response.json();
  return data.answer;
}

// Usage
const answer = await askQuestion('What are MongoDB best practices?');
console.log(answer);
```

### React Hook

```jsx
import { useState } from 'react';

function useRAG() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const query = async (question, sessionId = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: question,
          session_id: sessionId,
          use_rerank: true
        })
      });
      
      const data = await response.json();
      return data.answer;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { query, loading, error };
}

// Usage in component
function ChatComponent() {
  const { query, loading } = useRAG();
  const [answer, setAnswer] = useState('');

  const handleSubmit = async (question) => {
    const result = await query(question, 'user-123');
    setAnswer(result);
  };

  return (
    <div>
      {loading ? 'Loading...' : answer}
    </div>
  );
}
```

### Vue.js

```javascript
export default {
  data() {
    return {
      query: '',
      answer: '',
      loading: false
    }
  },
  methods: {
    async askQuestion() {
      this.loading = true;
      
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: this.query,
          session_id: 'vue-user',
          use_rerank: false
        })
      });
      
      const data = await response.json();
      this.answer = data.answer;
      this.loading = false;
    }
  }
}
```

---

## 🔧 Use from Backend

### Node.js/Express

```javascript
const express = require('express');
const fetch = require('node-fetch');

const app = express();
app.use(express.json());

// Proxy endpoint for your frontend
app.post('/api/ask', async (req, res) => {
  try {
    const { question, userId } = req.body;
    
    const response = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: question,
        session_id: userId,
        use_rerank: true
      })
    });
    
    const data = await response.json();
    res.json({ answer: data.answer });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

### Python/Flask

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    user_id = data.get('userId')
    
    # Call RAG API
    response = requests.post('http://localhost:8000/query', json={
        'query': question,
        'session_id': user_id,
        'use_rerank': True
    })
    
    result = response.json()
    return jsonify({'answer': result['answer']})

if __name__ == '__main__':
    app.run(port=3000)
```

---

## 📊 API Features

### ✅ Conversation Memory
Maintain context across multiple questions using `session_id`:

```javascript
// First question
await query({ query: "Tell me about backups", session_id: "user123" });

// Follow-up (remembers context)
await query({ query: "What did I just ask?", session_id: "user123" });
```

### ✅ Result Reranking
Improve answer quality with reranking:

```javascript
await query({ 
  query: "MongoDB best practices", 
  use_rerank: true  // Better results!
});
```

### ✅ Metadata Filtering
Filter by product, content type, or date:

```javascript
await query({ 
  query: "Best practices",
  filter_criteria: {
    "metadata.productName": "MongoDB Atlas"
  }
});
```

---

## 🚀 Production Deployment

### Using Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "api.py"]
```

2. Build and run:
```bash
docker build -t rag-api .
docker run -p 8000:8000 --env-file .env rag-api
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Environment Variables

The API reads from `.env`:
- `MONGODB_URI` - MongoDB connection string
- `PROXY_ENDPOINT` - LLM proxy URL
- `VOYAGE_API_KEY` - Voyage AI API key

---

## 📝 Response Format

All endpoints return JSON:

```json
{
  "answer": "Based on the context provided...",
  "session_id": "user123"
}
```

Errors:
```json
{
  "detail": "Error message here"
}
```

---

## 🔒 CORS Configuration

The API allows all origins for development. For production, update `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📖 Full Documentation

- **API Usage Guide**: See `API_USAGE.md`
- **Interactive Docs**: http://localhost:8000/docs
- **Original README**: See `README.md`

---

## 🎯 Next Steps

1. ✅ API is running
2. 🔨 Build your frontend app (or use the separate frontend repository)
3. 📱 Integrate with your mobile app
4. 🚀 Deploy to production

---

## 🐛 Troubleshooting

### API won't start

```bash
# Make sure MongoDB container is running
docker ps | grep mongodb

# Check if port 8000 is available
lsof -i :8000

# Verify environment variables
cat .env
```

### CORS errors in browser

The API allows all origins by default. If you still see CORS errors, make sure you're using the correct URL (`http://localhost:8000`).

### Can't connect from frontend

Make sure:
1. API is running: `curl http://localhost:8000/health`
2. Using correct URL in frontend code
3. No firewall blocking localhost connections

---

## 💡 Tips

- **Development**: Use `--reload` flag for auto-restart on code changes
- **Performance**: Use reranking for better (but slightly slower) results
- **Memory**: Use session IDs to maintain conversation context
- **Monitoring**: Check `/stats` endpoint for system information

---

**Your RAG application is now an API! 🎉**

Try it out: `open http://localhost:8000/docs`

