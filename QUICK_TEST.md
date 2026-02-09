# Quick Test Guide

## Fastest Way to Test

### 1. Start Ollama (Terminal 1)
```bash
ollama serve
```

### 2. Pull a Model (if not already done)
```bash
ollama pull mistral
```

### 3. Start the App (Terminal 2)
```bash
# Option A: Use the quick start script
./start.sh

# Option B: Manual start
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 4. Open Browser
Go to: **http://localhost:8000**

---

## 5-Minute Test Flow

### Test 1: URL Extraction (Fastest)
1. Click **"Website URL"** tab
2. Enter: `https://en.wikipedia.org/wiki/Python_(programming_language)`
3. Click **"Extract text from URL"**
4. ✅ Should see content preview

### Test 2: Generate Quiz
1. After extraction, you're on "Quiz Settings"
2. Select **Difficulty: Medium**
3. Set **Questions: 5** (fewer = faster)
4. Click **"Generate Quiz"**
5. ⏳ Wait 30-60 seconds
6. ✅ Quiz should appear

### Test 3: Take Quiz
1. Answer all questions (click radio buttons)
2. Click **"Submit Quiz"**
3. ✅ See your score

---

## Test with PDF

1. Find any PDF with text (not scanned images)
2. Click **"PDF Upload"** tab
3. Upload the PDF
4. Click **"Extract text from PDF"**
5. Follow steps above to generate quiz

---

## Verify Everything Works

### Check Ollama:
```bash
curl http://localhost:11434/api/tags
```
Should return JSON with your models.

### Check Backend:
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"ok"}`

### Check API Docs:
Open: http://localhost:8000/docs
Should see interactive API documentation.

---

## Common Issues

**"Failed to reach Ollama"**
→ Make sure `ollama serve` is running

**"Model not found"**
→ Run `ollama pull mistral`

**Port 8000 in use**
→ Change port in `backend/main.py` line 147

**Frontend not loading**
→ Check backend is running, check browser console (F12)

---

## What to Expect

- **Text extraction:** 1-5 seconds
- **Quiz generation:** 30-90 seconds (first time slower)
- **Quiz submission:** Instant
- **Share link:** Works immediately

---

## Success Criteria

✅ Can extract text from URL  
✅ Can extract text from PDF  
✅ Can generate quiz (takes time, be patient!)  
✅ Quiz questions are relevant to content  
✅ Can submit and see score  
✅ Share link works  

If all these work, your setup is correct! 🎉
