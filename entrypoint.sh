#!/bin/bash
set -e

export PYTHONPATH=$PYTHONPATH:/app/src

# Wait for database availability (simple wait, in prod use wait-for-it)
echo "Waiting for database..."
sleep 5

# Run database migrations
echo "Running migrations..."
alembic upgrade head

# Seed initial data if needed (optional, checking if admin exists logic is inside seed)
echo "Seeding database..."
python -m backend.seed

# Start the application
echo "Starting application..."
exec uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
