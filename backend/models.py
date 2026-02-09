from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Text

from database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String(16), nullable=False)  # "pdf" | "url" | "text"
    source_label = Column(Text, nullable=True)  # filename or URL

    difficulty = Column(String(8), nullable=False)
    num_questions = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)  # extracted text (possibly truncated)
    questions_json = Column(Text, nullable=False)  # JSON list of questions

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String(36), nullable=False)

    answers_json = Column(Text, nullable=False)  # JSON: {index: "A"/"B"/"C"/"D"}
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

