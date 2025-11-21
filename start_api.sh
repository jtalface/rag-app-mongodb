#!/bin/bash

# Start the RAG API Server
# Usage: ./start_api.sh [--reload] [--port 8000]

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Parse arguments
RELOAD=""
PORT="8000"

while [[ $# -gt 0 ]]; do
  case $1 in
    --reload)
      RELOAD="--reload"
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./start_api.sh [--reload] [--port 8000]"
      exit 1
      ;;
  esac
done

echo "🚀 Starting RAG API Server..."
echo "📍 http://localhost:${PORT}"
echo "📚 API Docs: http://localhost:${PORT}/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python api.py --host 0.0.0.0 --port ${PORT} ${RELOAD}

