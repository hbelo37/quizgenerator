# Testing Guide - MCQ Quiz Generator

This guide will help you test the application step-by-step.

## Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed and running locally
3. **A PDF file** or **a website URL** to test with

---

## Step 1: Install Ollama

### macOS/Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows:
Download from: https://ollama.ai/download

### Pull a model:
```bash
ollama pull mistral
# OR
ollama pull llama3
```

### Start Ollama server:
```bash
ollama serve
```
**Keep this terminal window open!** Ollama must be running.

---

## Step 2: Setup Python Environment

Open a **new terminal** (keep Ollama running in the first one):

```bash
# Navigate to project directory
cd "Quiz generator"

# Create virtual environment
cd backend
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1
# Windows CMD:
# venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Start the Backend Server

Still in the `backend` directory with venv activated:

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open too!**

---

## Step 4: Open the Application

Open your browser and go to:
```
http://localhost:8000
```

You should see the MCQ Quiz Generator interface.

---

## Step 5: Test PDF Upload

### Test 1: Upload a PDF

1. Click the **"📄 PDF Upload"** tab (should be selected by default)
2. Click the upload area or drag & drop a PDF file
3. Select a PDF file (any PDF with text content works)
4. Click **"Extract text from PDF"**
5. **Expected:** You should see:
   - Status message: "Text extracted successfully."
   - Content preview appears below
   - Page automatically moves to "Quiz Settings" step

### Test 2: Invalid PDF

1. Try uploading a non-PDF file (e.g., .txt, .jpg)
2. **Expected:** Error message: "File must be a PDF."

---

## Step 6: Test URL Extraction

1. Click the **"🌐 Website URL"** tab
2. Enter a URL, for example:
   - `https://en.wikipedia.org/wiki/Python_(programming_language)`
   - `https://www.python.org/about/`
3. Click **"Extract text from URL"**
4. **Expected:** 
   - Status: "Text extracted successfully."
   - Content preview appears
   - Moves to "Quiz Settings" step

### Test Invalid URL:
1. Enter invalid URL like `not-a-url`
2. **Expected:** Error message

---

## Step 7: Generate a Quiz

After extracting content (from PDF or URL):

1. **Select Difficulty:**
   - Choose: **Easy**, **Medium**, or **Hard**

2. **Set Number of Questions:**
   - Enter a number between 5-50 (default: 10)

3. Click **"Generate Quiz"**

4. **Expected:**
   - Status: "Generating quiz with local LLM… this may take a minute."
   - Wait 30-60 seconds (depending on your machine)
   - Quiz appears with all questions displayed
   - Share link is generated

### What to Check:
- ✅ Questions are relevant to the source content
- ✅ Each question has exactly 4 options (A, B, C, D)
- ✅ Questions match the selected difficulty level
- ✅ No obvious hallucinations (questions should be based on the text)

---

## Step 8: Take the Quiz

1. **Answer questions** by clicking radio buttons
2. Click **"Submit Quiz"**
3. **Expected:**
   - Results page shows:
     - Score (e.g., "Score: 7 / 10")
     - Percentage (e.g., "Accuracy: 70.0%")
   - Share link is displayed

---

## Step 9: Test Shareable Link

1. After generating a quiz, copy the share link
2. Open it in a **new browser tab** or **incognito window**
3. **Expected:**
   - Quiz loads directly (no need to re-upload content)
   - You can take the quiz
   - Submit works normally

---

## Step 10: Test API Endpoints Directly

You can also test the API using curl or Postman:

### Health Check:
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status":"ok"}`

### Upload PDF:
```bash
curl -X POST http://localhost:8000/upload/pdf \
  -F "file=@/path/to/your/file.pdf"
```
**Expected:** JSON with `content` field

### Upload URL:
```bash
curl -X POST http://localhost:8000/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Generate Quiz:
```bash
curl -X POST http://localhost:8000/generate-quiz \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your long text content here...",
    "source_type": "text",
    "source_label": null,
    "difficulty": "medium",
    "num_questions": 5
  }'
```

### Get Quiz:
```bash
curl http://localhost:8000/quiz/{quiz_id}
```

### Submit Quiz:
```bash
curl -X POST http://localhost:8000/submit-quiz \
  -H "Content-Type: application/json" \
  -d '{
    "quiz_id": "your-quiz-id",
    "answers": {"0": "A", "1": "B", "2": "C"}
  }'
```

---

## API Documentation

Visit: **http://localhost:8000/docs**

This is FastAPI's automatic interactive API documentation. You can test all endpoints here!

---

## Troubleshooting

### Issue: "Failed to reach Ollama"
**Solution:**
- Make sure Ollama is running: `ollama serve`
- Check Ollama is accessible: `curl http://localhost:11434/api/tags`
- Verify model is installed: `ollama list`

### Issue: "LLM response did not contain JSON"
**Solution:**
- The model might be generating text instead of JSON
- Try a different model: `ollama pull llama3` and update `backend/config.py`:
  ```python
  OLLAMA_MODEL = "llama3"
  ```

### Issue: "Content too short"
**Solution:**
- Make sure your PDF/URL has enough text content (at least 50 characters)
- Try a longer article or document

### Issue: Frontend not loading
**Solution:**
- Check backend is running on port 8000
- Check browser console for errors (F12)
- Verify `frontend/` folder exists in project root

### Issue: Database errors
**Solution:**
- Delete `data/quiz.db` and restart the server (it will recreate)
- Check `data/` folder exists and is writable

### Issue: Port 8000 already in use
**Solution:**
- Change port in `backend/main.py`:
  ```python
  uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
  ```
- Update frontend `API_BASE` if needed

---

## Quick Test Checklist

- [ ] Ollama is running (`ollama serve`)
- [ ] Model is pulled (`ollama list` shows mistral/llama3)
- [ ] Backend server is running (`python main.py` in backend/)
- [ ] Can access http://localhost:8000
- [ ] Can upload PDF and extract text
- [ ] Can extract text from URL
- [ ] Can generate quiz (takes 30-60 seconds)
- [ ] Quiz questions are relevant to content
- [ ] Can submit quiz and see results
- [ ] Share link works in new tab

---

## Performance Notes

- **First quiz generation:** May take 60-90 seconds (model loading)
- **Subsequent generations:** Usually 20-40 seconds
- **Large PDFs:** May take longer to extract text
- **Complex URLs:** May timeout if site is slow

---

## Next Steps

Once testing is complete:
1. Try different difficulty levels
2. Test with various PDFs and URLs
3. Share quiz links with others
4. Check the database: `sqlite3 data/quiz.db` to see stored quizzes

---

## Need Help?

Check:
- Backend logs in terminal where `python main.py` is running
- Browser console (F12 → Console tab)
- Ollama logs if generation fails
