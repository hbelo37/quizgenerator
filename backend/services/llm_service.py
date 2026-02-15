from __future__ import annotations

import json
import ast
import re
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

        try:
            return self._parse_questions(raw, expected=num_questions)
        except RuntimeError:
            try:
                repaired = self._repair_to_json(raw, num_questions)
                return self._parse_questions(repaired, expected=num_questions)
            except RuntimeError:
                return self._build_fallback_questions(content, num_questions)

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
        blob = self._extract_json_blob(raw)
        if blob is None:
            # Last fallback: try parsing common plaintext MCQ format.
            plaintext_questions = self._parse_plaintext_questions(raw, expected)
            if plaintext_questions:
                return plaintext_questions
            raise RuntimeError("LLM response did not contain JSON.")

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

    def _extract_json_blob(self, raw: str) -> Dict[str, Any] | None:
        # Prefer fenced ```json blocks when present.
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw, re.IGNORECASE)
        candidates: List[str] = []
        if fence_match:
            candidates.append(fence_match.group(1))

        # Generic object candidate.
        obj_start = raw.find("{")
        obj_end = raw.rfind("}") + 1
        if obj_start != -1 and obj_end > obj_start:
            candidates.append(raw[obj_start:obj_end])

        # Some models return only an array.
        arr_start = raw.find("[")
        arr_end = raw.rfind("]") + 1
        if arr_start != -1 and arr_end > arr_start:
            candidates.append('{"questions": ' + raw[arr_start:arr_end] + "}")

        for candidate in candidates:
            # Normalize smart quotes that often break JSON parsing.
            normalized = (
                candidate.replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("‘", "'")
            )

            try:
                parsed = json.loads(normalized)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                # Fall back to python-literal parsing for pseudo-JSON output.
                try:
                    parsed = ast.literal_eval(normalized)
                    if isinstance(parsed, list):
                        return {"questions": parsed}
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue
        return None

    def _parse_plaintext_questions(self, raw: str, expected: int) -> List[Dict[str, Any]]:
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        question_re = re.compile(r"^(?:Q(?:uestion)?\s*)?(\d+)[\)\.\:\-]\s+(.+)$", re.IGNORECASE)
        option_re = re.compile(r"^([A-D])[\)\.\:\-]\s+(.+)$", re.IGNORECASE)
        answer_re = re.compile(r"^(?:answer|correct(?:\s+answer)?)\s*[:\-]?\s*([A-D])\b", re.IGNORECASE)

        parsed: List[Dict[str, Any]] = []
        current_question = ""
        current_options: Dict[str, str] = {}
        current_answer = "A"

        def flush_current() -> None:
            nonlocal current_question, current_options, current_answer
            if current_question and len(current_options) == 4:
                parsed.append(
                    {
                        "question": current_question,
                        "options": [
                            current_options.get("A", ""),
                            current_options.get("B", ""),
                            current_options.get("C", ""),
                            current_options.get("D", ""),
                        ],
                        "correct_answer": current_answer,
                    }
                )
            current_question = ""
            current_options = {}
            current_answer = "A"

        for line in lines:
            qm = question_re.match(line)
            if qm:
                flush_current()
                current_question = qm.group(2).strip()
                continue

            om = option_re.match(line)
            if om and current_question:
                current_options[om.group(1).upper()] = om.group(2).strip()
                continue

            am = answer_re.match(line)
            if am and current_question:
                current_answer = am.group(1).upper()

        flush_current()
        return parsed[:expected]

    def _repair_to_json(self, raw: str, expected: int) -> str:
        # Ask the model to convert arbitrary output into strict JSON.
        repair_prompt = f"""
Convert the following quiz text into strict JSON.
Return only JSON with this shape:
{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A"
    }}
  ]
}}
Keep at most {expected} questions.

Input:
\"\"\"{raw[:12000]}\"\"\"
"""

        if self.provider == "ollama":
            url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            resp = requests.post(
                url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": repair_prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
                timeout=180,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"Ollama repair failed: {resp.status_code} {resp.text}")
            data = resp.json()
            return str(data.get("response", ""))

        if self.provider == "huggingface":
            base_url = HUGGINGFACE_API_URL.rstrip("/")
            if "api-inference.huggingface.co" in base_url:
                base_url = base_url.replace(
                    "https://api-inference.huggingface.co",
                    "https://router.huggingface.co/hf-inference",
                )
            model = HUGGINGFACE_MODEL.strip().strip("/")
            chat_url = f"{base_url}/{model}/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            if HUGGINGFACE_API_TOKEN:
                headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": repair_prompt}],
                "temperature": 0.1,
                "max_tokens": max(512, expected * 160),
            }
            resp = requests.post(chat_url, headers=headers, json=payload, timeout=180)
            if resp.status_code >= 400:
                raise RuntimeError(f"Hugging Face repair failed: {resp.status_code} {resp.text[:500]}")
            data = resp.json()
            if isinstance(data, dict):
                choices = data.get("choices")
                if isinstance(choices, list) and choices:
                    first = choices[0]
                    if isinstance(first, dict):
                        message = first.get("message")
                        if isinstance(message, dict) and "content" in message:
                            return str(message["content"])
            raise RuntimeError("Hugging Face repair failed: unexpected response format.")

        raise RuntimeError("Unsupported LLM provider for repair step.")

    def _build_fallback_questions(self, content: str, expected: int) -> List[Dict[str, Any]]:
        """Build simple MCQs from source text when model output is unusable."""
        lines = [ln.strip() for ln in re.split(r"[.\n]+", content) if ln.strip()]
        # Keep medium-length candidate statements.
        candidates = [ln for ln in lines if 60 <= len(ln) <= 220]
        if not candidates:
            candidates = lines[: max(1, expected)]

        question_words = [
            "primary",
            "main",
            "best",
            "key",
            "most likely",
            "core",
            "central",
            "important",
        ]
        fallback_questions: List[Dict[str, Any]] = []
        seen = set()

        for idx, sentence in enumerate(candidates):
            if len(fallback_questions) >= expected:
                break
            sentence_clean = " ".join(sentence.split())
            if sentence_clean.lower() in seen:
                continue
            seen.add(sentence_clean.lower())

            words = sentence_clean.split()
            if len(words) < 8:
                continue

            answer = sentence_clean
            # Build distractors by simple controlled edits.
            distractors = [
                sentence_clean.replace(words[0], question_words[idx % len(question_words)], 1),
                sentence_clean.replace(words[-1], "concept", 1),
                f"{sentence_clean} This statement is unrelated to the source.",
            ]
            options = [answer] + distractors
            # Keep unique options.
            unique_options: List[str] = []
            for opt in options:
                opt_clean = " ".join(opt.split())
                if opt_clean not in unique_options:
                    unique_options.append(opt_clean)
            while len(unique_options) < 4:
                unique_options.append(f"None of these statements matches the text exactly ({len(unique_options)+1}).")
            unique_options = unique_options[:4]

            fallback_questions.append(
                {
                    "question": f"Which statement is directly supported by the provided text? ({len(fallback_questions)+1})",
                    "options": unique_options,
                    "correct_answer": "A",
                }
            )

        if not fallback_questions:
            raise RuntimeError("Unable to generate questions from provided content.")

        return fallback_questions[:expected]
