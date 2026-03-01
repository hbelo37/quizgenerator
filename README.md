# AI Quiz Generator

## Problem
Students are tired of passive revision and want active recall-based testing.

## Solution
Built a tool that converts notes into MCQs using LLM APIs.

## Target User
12th-grade students preparing for board exams.

## Features
- Upload notes
- Auto-generate MCQs
- Difficulty control
- Instant scoring

## Tech Stack
React + Node + GROQ API

## Product Decisions
- Chose MCQ over subjective for faster validation
- Kept UI minimal to reduce cognitive load

## Future Improvements
- Adaptive difficulty
- Analytics dashboard

## Project structure

```text
backend/
  main.py              # FastAPI app (API + static frontend)
  config.py            # Paths, SQLite URL, LLM config
  database.py          # SQLAlchemy engine + session + init_db()
  models.py            # Quiz + QuizResponse SQLAlchemy models
  schemas.py           # Pydantic request/response models
  services/
    __init__.py
    langextract.py     # "LangExtract" style text extraction module
    llm_service.py     # Ollama integration + prompt and JSON parsing
    quiz_service.py    # Quiz generation, retrieval, and grading logic
  requirements.txt

frontend/
  index.html           # Single-page UI (input → settings → quiz → results)
  style.css
  script.js

data/
  quiz.db              # SQLite database (auto‑created)

uploads/
  (temporary PDF storage, auto‑created)
```

---

## API endpoints

All endpoints are served by FastAPI (see `backend/main.py`):

- **`POST /upload/pdf`**
  - `multipart/form-data` with field `file` (PDF)
  - Uses `LangExtract.from_pdf` to extract text
  - Returns: `{ "content": "<extracted text (truncated)>" }`

- **`POST /upload/url`**
  - JSON body: `{ "url": "https://example.com/article" }`
  - Uses `LangExtract.from_url` to extract text
  - Returns: `{ "content": "<extracted text (truncated)>" }`

- **`POST /generate-quiz`**
  - JSON body:

    ```json
    {
      "content": "long extracted text…",
      "source_type": "text",
      "source_label": "optional label",
      "difficulty": "easy | medium | hard",
      "num_questions": 10
    }
    ```

  - Calls local LLM via `LLMService` (Ollama) with a strict JSON‑only prompt
  - Persists quiz + questions into SQLite
  - Returns:

    ```json
    {
      "quiz_id": "uuid",
      "questions": [
        {
          "question": "…",
          "options": ["A", "B", "C", "D"],
          "correct_answer": "A"
        }
      ]
    }
    ```

- **`GET /quiz/{quiz_id}`**
  - Returns the quiz for taking, **without** revealing correct answers:

    ```json
    {
      "quiz_id": "uuid",
      "difficulty": "medium",
      "num_questions": 10,
      "questions": [
        { "index": 0, "question": "…", "options": ["A", "B", "C", "D"] }
      ]
    }
    ```

- **`POST /submit-quiz`**
  - JSON body:

    ```json
    {
      "quiz_id": "uuid",
      "answers": { "0": "A", "1": "C" }
    }
    ```

  - Looks up quiz, compares user answers, stores a `QuizResponse`
  - Returns:

    ```json
    { "score": 7, "total": 10, "percentage": 70.0 }
    ```

- **`GET /health`**
  - Simple health check: `{ "status": "ok" }`

---

## LLM prompt (core idea)

The prompt used by `LLMService` (see `backend/services/llm_service.py`) is designed to:

- Enforce **grounding**: “Base ONLY on the provided text; do NOT hallucinate”
- Enforce **difficulty**:
  - **easy**: factual, direct questions
  - **medium**: conceptual, understanding‑based
  - **hard**: analytical, tricky but fair distractors
- Enforce **output shape**: strict JSON with `questions` list, each having:
  - `question`
  - `options` (4 strings)
  - `correct_answer` (`"A" | "B" | "C" | "D"` or option text)

You can inspect and tweak the exact wording in `LLMService._build_prompt`.

---

## Running locally (zero cost)

### 1. Install Python + Ollama

- Python **3.10+**
- Install **Ollama** from their site and pull a free model, e.g.:

```bash
ollama pull mistral
```

Then start the Ollama server in a terminal:

```bash
ollama serve
```

This exposes a local HTTP API at `http://localhost:11434` (no API keys, no cost).

### 2. Install backend dependencies

From the project root (`Quiz generator`):

```bash
cd backend
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Run the FastAPI app

Still inside `backend` and with the venv active:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

FastAPI will:

- Expose the API on `http://localhost:8000`
- Serve the frontend static files from `../frontend` at the root path (`/`)

Open your browser at:

- **UI**: `http://localhost:8000/`
- **Docs**: `http://localhost:8000/docs`

---

## Using the app

1. **Input**
   - Choose **PDF upload** or **Website URL**
   - Click “Extract text …” – content is processed by `LangExtract`
   - A preview of the extracted text appears

2. **Quiz settings**
   - Choose difficulty: **Easy / Medium / Hard**
   - Choose number of questions (5–50)
   - Click **Generate quiz**
   - Backend calls Ollama to generate questions, stores quiz in SQLite, and returns quiz ID + questions

3. **Take quiz**
   - Answer questions in the browser
   - Click **Submit quiz** to see score and percentage

4. **Share**
   - Copy the shareable link from the results screen
   - Anyone on your machine (or network, if you expose the port) can open the link, which loads the quiz via `GET /quiz/{quiz_id}`

---

## Notes / configuration

- To change the LLM model or base URL, set environment variables before starting FastAPI:

  ```bash
  export LLM_PROVIDER=huggingface
  export HUGGINGFACE_API_TOKEN=your_hf_token
  export HUGGINGFACE_MODEL=google/flan-t5-base
  ```

- For local Ollama instead, use:
  ```bash
  export LLM_PROVIDER=ollama
  export OLLAMA_MODEL=llama3
  export OLLAMA_BASE_URL=http://localhost:11434
  ```

---

## License

This project is intended to be fully open‑source and free to run locally. You can adapt it as a boilerplate
for your own quiz generators or other document‑to‑question pipelines using only local models.
