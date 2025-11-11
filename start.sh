#!/bin/bash
# Railway startup script

# Get port from environment or use default
PORT="${PORT:-8000}"

echo "Starting FastAPI on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
