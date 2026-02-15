from typing import Dict, List

from pydantic import BaseModel, Field, HttpUrl, constr

from config import DIFFICULTIES, MIN_QUESTIONS, MAX_QUESTIONS


class UploadUrlRequest(BaseModel):
    url: HttpUrl


class UploadUrlResponse(BaseModel):
    content: str = Field(..., description="Extracted text (truncated for preview)")


class UploadPdfResponse(BaseModel):
    content: str = Field(..., description="Extracted text (truncated for preview)")


class GenerateQuizRequest(BaseModel):
    content: constr(min_length=50)
    source_type: constr(strip_whitespace=True) = "text"
    source_label: str | None = None
    difficulty: constr(strip_whitespace=True) = "medium"
    num_questions: int = Field(15, ge=MIN_QUESTIONS, le=MAX_QUESTIONS)

    def normalised_difficulty(self) -> str:
        d = self.difficulty.strip().lower()
        if d not in DIFFICULTIES:
            d = "medium"
        return d


class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str


class GenerateQuizResponse(BaseModel):
    quiz_id: str
    questions: List[Question]


class QuizPublicQuestion(BaseModel):
    index: int
    question: str
    options: List[str]


class GetQuizResponse(BaseModel):
    quiz_id: str
    difficulty: str
    num_questions: int
    questions: List[QuizPublicQuestion]


class SubmitQuizRequest(BaseModel):
    quiz_id: str
    answers: Dict[int, str]


class SubmitQuizResponse(BaseModel):
    score: int
    total: int
    percentage: float

