# Fix: "The executable `cd` could not be found"

## Problem
Railway/Docker can't find `cd` because it's a shell builtin, not an executable.

## Solution Applied

I've updated the config files to use proper shell syntax:

### Option 1: Use the startup script (Recommended)

Update Railway settings:
- **Start Command**: `sh backend/start.sh`
- **Root Directory**: (leave empty)

### Option 2: Use absolute path in Dockerfile

The Dockerfile now uses:
```dockerfile
CMD ["sh", "-c", "cd /app/backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Option 3: Set working directory in Dockerfile

Or change Dockerfile to:
```dockerfile
WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Quick Fix in Railway Dashboard

1. Go to Railway → Your Service → Settings
2. Under **Deploy**:
   - **Start Command**: `sh -c 'cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT'`
3. Save and redeploy

Or use the startup script:
- **Start Command**: `sh backend/start.sh`
