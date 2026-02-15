# Deployment Guide - MCQ Quiz Generator

This guide will help you deploy the app online for free so you can share it with others.

## Deployment Strategy

- **Frontend (React)**: Deploy to Vercel or Netlify (FREE)
- **Backend (FastAPI)**: Deploy to Render or Railway (FREE tier available)
- **Database**: SQLite (included with backend)
- **LLM**: Ollama (needs to run on backend server)

---

## Option 1: Deploy to Render (Recommended - Easiest)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Backend to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `mcq-quiz-backend`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Environment Variables**:
     ```
     PORT=10000
     ```
5. Click **"Create Web Service"**

**Note**: Render free tier spins down after 15 minutes of inactivity. For always-on, you'll need a paid plan or use Railway.

### Step 3: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: `Create React App`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Environment Variables**:
     ```
     REACT_APP_API_BASE=https://your-backend-url.onrender.com
     ```
5. Click **"Deploy"**

---

## Option 2: Deploy to Railway (Always-On Free Trial)

### Step 1: Deploy Backend

1. Go to [railway.app](https://railway.app) and sign up
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will auto-detect Python
5. Add environment variable:
   ```
   PORT=8000
   ```
6. Railway will automatically deploy

### Step 2: Deploy Frontend

1. In Railway, click **"New"** → **"GitHub Repo"**
2. Select same repository
3. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npx serve -s build -l $PORT`
   - **Environment Variables**:
     ```
     REACT_APP_API_BASE=https://your-backend-url.railway.app
     PORT=3000
     ```

---

## Option 3: Deploy to Fly.io (Free Tier Available)

### Backend Setup

1. Install Fly CLI: `brew install flyctl` (or see fly.io/docs)
2. Login: `flyctl auth login`
3. In `backend/` directory, create `fly.toml`:

```toml
app = "mcq-quiz-backend"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

4. Deploy: `flyctl deploy`

### Frontend Setup

1. In `frontend/` directory, create `fly.toml`:

```toml
app = "mcq-quiz-frontend"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"
  REACT_APP_API_BASE = "https://mcq-quiz-backend.fly.dev"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

2. Deploy: `flyctl deploy`

---

## Important: Ollama Setup for Production

**Problem**: Ollama needs to run on the backend server, but most free hosting doesn't allow installing system packages.

### Solution Options:

#### Option A: Use HuggingFace Inference API (FREE)

Update `backend/services/llm_service.py` to use HuggingFace's free inference API:

```python
def _call_huggingface_api(self, prompt: str) -> str:
    """Use HuggingFace free inference API"""
    import requests
    
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {"Authorization": "Bearer YOUR_HF_TOKEN"}  # Get free token from hf.co
    
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return response.json()[0]["generated_text"]
```

#### Option B: Use OpenAI-Compatible API (Free Tier)

Use services like:
- **Together.ai** (free tier)
- **Groq** (free tier, very fast)
- **Anthropic Claude** (free tier)

Update `backend/config.py`:
```python
LLM_PROVIDER = "openai_compatible"
OPENAI_API_BASE = "https://api.groq.com/openai/v1"
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "llama-3-8b-8192"
```

#### Option C: Self-Host Backend (VPS)

Use a VPS like:
- **DigitalOcean Droplet** ($6/month)
- **Linode** ($5/month)
- **Hetzner** (€4/month)

Then install Ollama on the VPS and deploy backend there.

---

## Quick Deploy Script

I've created deployment configs. Here's what to do:

### 1. Update Backend for Production

Create `backend/Procfile` (for Render/Railway):
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 2. Update Frontend Environment

Create `frontend/.env.production`:
```
REACT_APP_API_BASE=https://your-backend-url.onrender.com
```

### 3. Deploy Commands

**Render (Backend)**:
```bash
# After connecting GitHub repo, Render will auto-deploy
# Just make sure PORT environment variable is set
```

**Vercel (Frontend)**:
```bash
cd frontend
vercel --prod
```

---

## Environment Variables Needed

### Backend:
- `PORT` (auto-set by hosting)
- `LLM_PROVIDER` (optional, defaults to "huggingface")
- `HUGGINGFACE_API_TOKEN` (recommended for Hugging Face free inference)
- `HUGGINGFACE_API_URL` (optional, defaults to `https://router.huggingface.co/hf-inference/models`)
- `HUGGINGFACE_MODEL` (optional, defaults to `google/flan-t5-base`)
- `OLLAMA_BASE_URL` (only if using Ollama)

### Frontend:
- `REACT_APP_API_BASE` (your backend URL)

---

## Testing After Deployment

1. **Backend Health Check**: `https://your-backend-url.onrender.com/health`
2. **API Docs**: `https://your-backend-url.onrender.com/docs`
3. **Frontend**: `https://your-frontend-url.vercel.app`

---

## Free Hosting Comparison

| Service | Free Tier | Always-On | Best For |
|---------|-----------|-----------|----------|
| **Render** | ✅ Yes | ❌ No (spins down) | Backend |
| **Railway** | ✅ Yes (trial) | ✅ Yes | Backend |
| **Vercel** | ✅ Yes | ✅ Yes | Frontend |
| **Netlify** | ✅ Yes | ✅ Yes | Frontend |
| **Fly.io** | ✅ Yes | ✅ Yes | Both |

---

## Recommended Setup

1. **Backend**: Railway (always-on free trial)
2. **Frontend**: Vercel (free, fast CDN)
3. **LLM**: Use HuggingFace free API or Groq free tier

This gives you a fully free, always-on deployment!

---

## Need Help?

Share your GitHub repo URL and I can help you set up the deployment configs!
