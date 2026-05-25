#!/bin/sh

# Run database migrations
alembic upgrade head

# Start application
uvicorn --host 0.0.0.0 --port 8000 backend.app:app
