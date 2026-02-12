# Troubleshooting: JSON Parse Error

## Error: "Unexpected end of JSON input"

This error means the backend returned an empty response or non-JSON content.

### Common Causes:

1. **Backend not running** - Check Railway dashboard
2. **Wrong API URL** - Check `REACT_APP_API_BASE` in Vercel
3. **CORS issue** - Backend might be blocking requests
4. **Backend error** - Check Railway logs

### How to Debug:

1. **Check Browser Console (F12)**:
   - Look for the actual API call
   - Check the response status
   - See the error details

2. **Check Backend URL**:
   - In Vercel → Settings → Environment Variables
   - `REACT_APP_API_BASE` should be: `https://your-backend.railway.app`
   - **No trailing slash!**

3. **Test Backend Directly**:
   - Open: `https://your-backend.railway.app/health`
   - Should return: `{"status":"ok"}`
   - If not, backend is down

4. **Check Railway Logs**:
   - Go to Railway → Your service → Logs
   - Look for errors when you try to generate quiz

5. **Test API Endpoint**:
   - Open: `https://your-backend.railway.app/docs`
   - Try the `/generate-quiz` endpoint manually
   - See what error it returns

### Quick Fixes:

**If backend URL is wrong:**
1. Vercel → Settings → Environment Variables
2. Update `REACT_APP_API_BASE`
3. Redeploy

**If backend is returning errors:**
- Check Railway logs
- Make sure Ollama/LLM is configured
- Check if database is initialized

**If CORS errors:**
- Backend already has CORS enabled
- Make sure `allow_origins=["*"]` in `backend/main.py`

### Test Commands:

```bash
# Test backend health
curl https://your-backend.railway.app/health

# Test quiz generation (replace with real content)
curl -X POST https://your-backend.railway.app/generate-quiz \
  -H "Content-Type: application/json" \
  -d '{"content":"Test content here","source_type":"text","difficulty":"medium","num_questions":5}'
```
