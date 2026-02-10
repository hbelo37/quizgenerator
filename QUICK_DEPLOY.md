# Quick Deploy Guide - Fix Docker Build Error

## Problem
Railway is trying to use Docker but `pip` command is not found.

## Solution Options

### Option 1: Use Nixpacks (Easiest - Recommended)

Railway will auto-detect Python if you have `nixpacks.toml`. I've created it for you!

**Steps:**
1. Update `railway.json` to use Nixpacks:
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     }
   }
   ```

2. Or delete `railway.json` - Railway will auto-detect `nixpacks.toml`

3. Deploy - Railway will use Nixpacks which handles Python automatically

### Option 2: Use Dockerfile (Current Setup)

I've created a proper `Dockerfile` that installs Python and pip.

**Steps:**
1. Make sure `railway.json` has:
   ```json
   {
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     }
   }
   ```

2. Deploy - Railway will use the Dockerfile

### Option 3: Manual Railway Setup (No Config Files)

1. Go to Railway dashboard
2. Click on your service
3. Go to **Settings** → **Build**
4. Set:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set **Root Directory**: Leave empty (or set to project root)
6. Railway will auto-detect Python

---

## Recommended: Use Nixpacks

**Why?** Nixpacks automatically:
- Detects Python version
- Installs dependencies
- Sets up the environment
- No Docker knowledge needed

**How:**
1. Delete or rename `railway.json` temporarily
2. Railway will use `nixpacks.toml` automatically
3. Deploy!

---

## Test Locally First

Test the Dockerfile locally:

```bash
# Build
docker build -t mcq-quiz-backend .

# Run
docker run -p 8000:8000 -e PORT=8000 mcq-quiz-backend
```

Test Nixpacks locally (if you have nixpacks CLI):
```bash
nixpacks build .
```

---

## Railway Environment Variables

Make sure these are set in Railway:

- `PORT` - Auto-set by Railway
- `LLM_PROVIDER` - Set to `ollama` or `openai_compatible`
- `OLLAMA_BASE_URL` - If using Ollama (won't work on Railway free tier)
- `OPENAI_API_BASE` - If using Groq/OpenAI-compatible API
- `OPENAI_API_KEY` - Your API key

---

## Quick Fix Right Now

**Simplest solution:**

1. In Railway dashboard → Your service → Settings
2. Under **Build & Deploy**:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Root Directory**: Leave empty
4. Click **Save**
5. Redeploy

This bypasses Docker entirely and uses Railway's built-in Python support!
