from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from config import (
    HUGGINGFACE_API_TOKEN,
    HUGGINGFACE_API_URL,
    HUGGINGFACE_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


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
        elif self.provider == "huggingface":
            raw = self._call_huggingface(content, num_questions, difficulty)
        else:
            raise RuntimeError("Unsupported LLM provider. Use 'ollama' or 'huggingface'.")

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

    def _call_huggingface(self, content: str, num_questions: int, difficulty: str) -> str:
        prompt = self._build_prompt(content, num_questions, difficulty)
        base_url = HUGGINGFACE_API_URL.rstrip("/")
        # Hugging Face migrated from api-inference.huggingface.co to router.huggingface.co.
        if "api-inference.huggingface.co" in base_url:
            base_url = base_url.replace(
                "https://api-inference.huggingface.co",
                "https://router.huggingface.co/hf-inference",
            )

        model = HUGGINGFACE_MODEL.strip().strip("/")
        chat_url = f"{base_url}/{model}/v1/chat/completions"
        legacy_url = f"{base_url}/{model}"
        headers = {"Content-Type": "application/json"}
        if HUGGINGFACE_API_TOKEN:
            headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"

        try:
            # Preferred path: OpenAI-compatible chat endpoint on HF router.
            chat_payload: Dict[str, Any] = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.3,
                "max_tokens": max(512, num_questions * 180),
            }
            resp = requests.post(chat_url, headers=headers, json=chat_payload, timeout=300)
        except Exception as exc:  # pragma: no cover - network error
            raise RuntimeError("Failed to reach Hugging Face inference endpoint.") from exc

        # Fallback for older text-generation style endpoints.
        if resp.status_code == 404:
            try:
                legacy_payload: Dict[str, Any] = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max(512, num_questions * 180),
                        "temperature": 0.3,
                        "return_full_text": False,
                    },
                }
                resp = requests.post(
                    legacy_url,
                    headers=headers,
                    json=legacy_payload,
                    timeout=300,
                )
            except Exception as exc:  # pragma: no cover - network error
                raise RuntimeError("Failed to reach Hugging Face legacy inference endpoint.") from exc

        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise RuntimeError(f"Hugging Face API error: {resp.status_code} {detail}")

        data = resp.json()
        if isinstance(data, dict):
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if isinstance(message, dict) and "content" in message:
                        return str(message["content"])

        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if "generated_text" in first:
                    return str(first["generated_text"])
        if isinstance(data, dict):
            if "generated_text" in data:
                return str(data["generated_text"])
            if "error" in data:
                raise RuntimeError(f"Hugging Face inference error: {data['error']}")

        raise RuntimeError("Unexpected response format from Hugging Face inference API.")

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
