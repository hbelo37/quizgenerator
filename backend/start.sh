#!/bin/sh
# Startup script for production

# Ensure we run from the backend directory (so imports like `from database import ...` work)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Wait for database to be ready (if needed)
# sleep 2

# Run migrations/init (if needed)
python -c "from database import init_db; init_db()" || true

# Start the server
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
