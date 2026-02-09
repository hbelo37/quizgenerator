from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL


class LLMService:
    """Wrapper around a local LLM (Ollama preferred)."""

    def __init__(self) -> None:
        self.provider = LLM_PROVIDER

    def generate_questions(
        self,
        content: str,
        num_questions: int,
        difficulty: str,
    ) -> List[Dict[str, Any]]:
        if self.provider == "ollama":
            raw = self._call_ollama(content, num_questions, difficulty)
        else:
            raise RuntimeError("Only 'ollama' provider is implemented in this template.")

        return self._parse_questions(raw, expected=num_questions)

    def _build_prompt(self, content: str, num_questions: int, difficulty: str) -> str:
        difficulty = difficulty.lower()
        if difficulty == "easy":
            difficulty_instructions = (
                "Ask factual, direct questions whose answers appear explicitly in the text."
            )
        elif difficulty == "hard":
            difficulty_instructions = (
                "Ask analytical, multi-step questions with tricky but fair distractors."
            )
        else:
            difficulty_instructions = (
                "Ask conceptual questions that require understanding and light reasoning."
            )

        truncated = content[:6000]

        return f"""
You are an MCQ quiz generator.

You will be given some source text. Based ONLY on that text, generate exactly {num_questions} multiple‑choice questions.

Rules:
- Difficulty: {difficulty.upper()} — {difficulty_instructions}
- Do NOT use any knowledge outside the provided text.
- Each question must have exactly 4 options.
- Options must be realistic and non‑trivial.
- Exactly one option is correct per question.
- Make sure the correct option is unambiguously supported by the text.

Return ONLY valid JSON, nothing else. The JSON must have this exact shape:
{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A"
    }}
  ]
}}

Source text:
\"\"\"{truncated}\"\"\""""

    def _call_ollama(self, content: str, num_questions: int, difficulty: str) -> str:
        prompt = self._build_prompt(content, num_questions, difficulty)
        url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        try:
            resp = requests.post(
                url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=300,
            )
        except Exception as exc:  # pragma: no cover - network error
            raise RuntimeError(
                f"Failed to reach Ollama at {OLLAMA_BASE_URL}. Is it running?"
            ) from exc

        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error: {resp.status_code} {resp.text}")

        data = resp.json()
        return data.get("response", "")

    def _parse_questions(self, raw: str, expected: int) -> List[Dict[str, Any]]:
        # Try to locate JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise RuntimeError("LLM response did not contain JSON.")

        try:
            blob = json.loads(raw[start:end])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse LLM JSON: {exc}") from exc

        questions = blob.get("questions")
        if not isinstance(questions, list) or not questions:
            raise RuntimeError("LLM JSON missing 'questions' list.")

        normalised: List[Dict[str, Any]] = []
        for q in questions:
            question = str(q.get("question", "")).strip()
            options = q.get("options") or []
            correct = str(q.get("correct_answer", "")).strip()

            if not question or not isinstance(options, list) or len(options) != 4:
                continue

            # accept either "A"/"B"/"C"/"D" or exact option text
            if correct.upper() in ("A", "B", "C", "D"):
                idx = {"A": 0, "B": 1, "C": 2, "D": 3}[correct.upper()]
            else:
                try:
                    idx = options.index(correct)
                except ValueError:
                    # default to first option if unclear
                    idx = 0

            normalised.append(
                {
                    "question": question,
                    "options": options,
                    "correct_answer": ["A", "B", "C", "D"][idx],
                }
            )

        if not normalised:
            raise RuntimeError("No valid questions parsed from LLM output.")

        return normalised[:expected]

