# Deploy Frontend to Vercel - Step by Step

## Quick Deploy (5 minutes)

### Step 1: Get Your Backend URL

1. Go to Railway dashboard
2. Click on your backend service
3. Copy the **Public URL** (looks like: `https://your-app.railway.app`)
4. Save this URL - you'll need it!

### Step 2: Deploy to Vercel

#### Option A: Via Vercel Dashboard (Easiest)

1. **Go to [vercel.com](https://vercel.com)** and sign up/login (use GitHub)

2. **Click "Add New Project"**

3. **Import your GitHub repository**
   - Select your `quizgenerator` repo
   - Click "Import"

4. **Configure Project:**
   - **Framework Preset**: `Create React App` (auto-detected)
   - **Root Directory**: `frontend` ⚠️ **IMPORTANT!**
   - **Build Command**: `npm run build` (auto-filled)
   - **Output Directory**: `build` (auto-filled)
   - **Install Command**: `npm install` (auto-filled)

5. **Environment Variables:**
   Click "Add" and add:
   - **Name**: `REACT_APP_API_BASE`
   - **Value**: `https://your-backend-url.railway.app` (paste your Railway backend URL)
   - Click "Add"

6. **Click "Deploy"**

7. **Wait 2-3 minutes** for build to complete

8. **Done!** Vercel gives you a URL like `https://your-app.vercel.app`

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Go to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy (follow prompts)
vercel

# Set production environment variable
vercel env add REACT_APP_API_BASE production
# When prompted, enter: https://your-backend-url.railway.app

# Deploy to production
vercel --prod
```

---

## Update Frontend to Use Backend URL

After deployment, make sure your frontend can reach the backend:

1. **In Vercel Dashboard:**
   - Go to your project → Settings → Environment Variables
   - Add/Update: `REACT_APP_API_BASE` = `https://your-backend-url.railway.app`
   - **Redeploy** after adding env vars

2. **Test the connection:**
   - Open your Vercel URL
   - Try generating a quiz
   - Check browser console (F12) for any API errors

---

## Troubleshooting

### CORS Errors

If you see CORS errors, make sure your backend `main.py` has:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific: ["https://your-frontend.vercel.app"]
    ...
)
```

### API Not Found (404)

- Check `REACT_APP_API_BASE` is set correctly in Vercel
- Make sure backend URL doesn't have trailing slash
- Redeploy frontend after changing env vars

### Build Fails

- Check `frontend/package.json` has all dependencies
- Make sure `npm install` runs successfully
- Check Vercel build logs for specific errors

---

## Your URLs After Deployment

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-backend.railway.app`
- **API Docs**: `https://your-backend.railway.app/docs`

---

## Share Your App!

Once deployed, share the Vercel URL with anyone - they can use your quiz generator!
