from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Body
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from config import MAX_FILE_SIZE_BYTES, UPLOAD_DIR
from database import get_db, init_db
from schemas import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    GetQuizResponse,
    SubmitQuizRequest,
    SubmitQuizResponse,
    UploadPdfResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from services.langextract import LangExtract
from services.quiz_service import QuizService

app = FastAPI(title="Free MCQ Quiz Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    # mount React build if present, otherwise mount source
    frontend_build = UPLOAD_DIR.parent / "frontend" / "build"
    frontend_src = UPLOAD_DIR.parent / "frontend"
    if frontend_build.exists():
        app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
    else:
        # Fallback: serve static files from src during development
        app.mount("/", StaticFiles(directory=str(frontend_src / "public"), html=True), name="frontend")


@app.post("/upload/pdf", response_model=UploadPdfResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadPdfResponse:
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="PDF too large (limit 50 MB).")

    tmp_path = UPLOAD_DIR / file.filename
    try:
        with open(tmp_path, "wb") as f:
            f.write(data)

        extracted = LangExtract.from_pdf(str(tmp_path), label=file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except Exception:
            pass

    # Return full content (client will use it for quiz generation)
    return UploadPdfResponse(content=extracted.text)


@app.post("/upload/url", response_model=UploadUrlResponse)
async def upload_url(payload: UploadUrlRequest) -> UploadUrlResponse:
    try:
        extracted = LangExtract.from_url(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Return full content (client will use it for quiz generation)
    return UploadUrlResponse(content=extracted.text)


@app.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest = Body(...),
    db: Session = Depends(get_db),
) -> GenerateQuizResponse:
    if len(request.content.strip()) < 50:
        raise HTTPException(
            status_code=400, detail="Content too short; please provide more text."
        )

    service = QuizService(db)
    result = service.generate_quiz(
        content=request.content,
        source_type=request.source_type,
        source_label=request.source_label,
        difficulty=request.normalised_difficulty(),
        num_questions=request.num_questions,
    )

    return GenerateQuizResponse(
        quiz_id=result["quiz_id"],
        questions=result["questions"],
    )


@app.get("/quiz/{quiz_id}", response_model=GetQuizResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db)) -> GetQuizResponse:
    service = QuizService(db)
    try:
        data = service.get_quiz_public(quiz_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return GetQuizResponse(**data)


@app.post("/submit-quiz", response_model=SubmitQuizResponse)
def submit_quiz(
    payload: SubmitQuizRequest,
    db: Session = Depends(get_db),
) -> SubmitQuizResponse:
    service = QuizService(db)
    try:
        result = service.submit_quiz(payload.quiz_id, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SubmitQuizResponse(
        score=result["score"],
        total=result["total"],
        percentage=result["percentage"],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

