#!/bin/bash
# Startup script for production

# Wait for database to be ready (if needed)
# sleep 2

# Run migrations/init (if needed)
python -c "from database import init_db; init_db()" || true

# Start the server
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
