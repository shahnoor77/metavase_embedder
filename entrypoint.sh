#!/bin/bash
set -e

echo "Waiting for app database..."
until pg_isready -h $APP_DB_HOST -p $APP_DB_PORT -U $APP_DB_USER; do
  echo "App database is unavailable - sleeping"
  sleep 2
done

echo "App database is up"

echo "Waiting for Metabase..."
until curl -f http://metabase:3000/api/health > /dev/null 2>&1; do
  echo "Metabase is unavailable - sleeping"
  sleep 5
done

echo "Metabase is up"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."

# Explicitly force polling in the shell environment
export WATCHFILES_FORCE_POLLING=true

# Start Uvicorn and tell it exactly which directory to watch
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app/app