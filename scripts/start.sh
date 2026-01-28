#!/bin/bash

# Configuration
FRONTEND_PORT=3001
BACKEND_PORT=8001
FRONTEND_PID_FILE=".frontend.pid"
FRONTEND_LOG="frontend.log"

echo "Starting Backend..."
docker-compose up -d --build
echo "Backend running (Docker)."

echo "Starting Frontend..."
cd frontend
# kill any existing process on port 3001 just in case
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

# Start Next.js in background
nohup npm run dev > ../$FRONTEND_LOG 2>&1 &
PID=$!
echo $PID > ../$FRONTEND_PID_FILE

echo "Frontend process launched (PID $PID). Logs: $FRONTEND_LOG"
echo "Application started!"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "Run 'make down' to stop."
