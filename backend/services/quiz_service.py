from __future__ import annotations

import json
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from config import DIFFICULTIES
from models import Quiz, QuizResponse
from services.llm_service import LLMService


class QuizService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMService()

    def generate_quiz(
        self,
        *,
        content: str,
        source_type: str,
        source_label: str | None,
        difficulty: str,
        num_questions: int,
    ) -> Dict[str, Any]:
        difficulty_norm = difficulty.lower()
        if difficulty_norm not in DIFFICULTIES:
            difficulty_norm = "medium"

        questions = self.llm.generate_questions(content, num_questions, difficulty_norm)

        quiz = Quiz(
            source_type=source_type,
            source_label=source_label,
            difficulty=difficulty_norm,
            num_questions=len(questions),
            content=content[:10000],  # truncate for storage
            questions_json=json.dumps(questions),
        )
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)

        return {"quiz_id": quiz.id, "questions": questions}

    def get_quiz_public(self, quiz_id: str) -> Dict[str, Any]:
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")

        questions: List[Dict[str, Any]] = json.loads(quiz.questions_json)
        public_questions = [
            {
                "index": idx,
                "question": q["question"],
                "options": q["options"],
            }
            for idx, q in enumerate(questions)
        ]

        return {
            "quiz_id": quiz.id,
            "difficulty": quiz.difficulty,
            "num_questions": len(public_questions),
            "questions": public_questions,
        }

    def submit_quiz(self, quiz_id: str, answers: Dict[int, str]) -> Dict[str, Any]:
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")

        questions: List[Dict[str, Any]] = json.loads(quiz.questions_json)
        score = 0
        results: List[Dict[str, Any]] = []

        for idx, q in enumerate(questions):
            user_answer = answers.get(idx)
            if user_answer is None:
                user_answer = answers.get(str(idx))  # defensive: JSON keys are often strings

            selected_letter = str(user_answer).upper() if user_answer is not None else None
            correct_letter = str(q.get("correct_answer", "A")).upper()
            options = q.get("options", [])

            def option_text(letter: str | None) -> str | None:
                if letter is None or letter not in ("A", "B", "C", "D"):
                    return None
                option_idx = {"A": 0, "B": 1, "C": 2, "D": 3}[letter]
                if isinstance(options, list) and len(options) > option_idx:
                    return str(options[option_idx])
                return None

            is_correct = selected_letter == correct_letter
            if is_correct:
                score += 1

            results.append(
                {
                    "index": idx,
                    "question": str(q.get("question", "")),
                    "selected_answer": selected_letter if selected_letter in ("A", "B", "C", "D") else None,
                    "selected_option": option_text(selected_letter),
                    "correct_answer": correct_letter if correct_letter in ("A", "B", "C", "D") else "A",
                    "correct_option": option_text(correct_letter) or "",
                    "is_correct": is_correct,
                }
            )

        total = len(questions)
        percentage = (score / total * 100.0) if total else 0.0

        response = QuizResponse(
            quiz_id=quiz_id,
            answers_json=json.dumps(answers),
            score=score,
            total=total,
        )
        self.db.add(response)
        self.db.commit()

        return {"score": score, "total": total, "percentage": percentage, "results": results}
