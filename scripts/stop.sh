#!/bin/bash

FRONTEND_PID_FILE=".frontend.pid"
FRONTEND_PORT=3001
BACKEND_PORT=8001

echo "Stopping Backend..."
docker-compose down
echo "Backend stopped."

echo "Stopping Frontend..."
if [ -f "$FRONTEND_PID_FILE" ]; then
    PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Killing Frontend process (PID $PID)..."
        kill $PID
    else
        echo "Frontend process $PID not found."
    fi
    rm "$FRONTEND_PID_FILE"
else
    echo "No frontend PID file found."
fi

# Cleanup ports just in case
echo "Cleaning up any stuck processes on ports $FRONTEND_PORT..."
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
echo "Shutdown complete."
