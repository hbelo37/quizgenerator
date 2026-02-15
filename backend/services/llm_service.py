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
            parsed = self._parse_questions(raw, expected=num_questions)
            if len(parsed) < num_questions:
                parsed.extend(
                    self._build_fallback_questions(
                        content,
                        num_questions - len(parsed),
                        difficulty=difficulty,
                    )
                )
            return parsed[:num_questions]
        except RuntimeError:
            try:
                repaired = self._repair_to_json(raw, num_questions)
                parsed = self._parse_questions(repaired, expected=num_questions)
                if len(parsed) < num_questions:
                    parsed.extend(
                        self._build_fallback_questions(
                            content,
                            num_questions - len(parsed),
                            difficulty=difficulty,
                        )
                    )
                return parsed[:num_questions]
            except RuntimeError:
                return self._build_fallback_questions(content, num_questions, difficulty=difficulty)

    def _build_prompt(self, content: str, num_questions: int, difficulty: str) -> str:
        difficulty = difficulty.lower()
        if difficulty == "easy":
            difficulty_instructions = (
                "Create factual recall questions only. Each answer must appear explicitly in the text."
            )
        elif difficulty == "hard":
            difficulty_instructions = (
                "Create analytical, multi-step questions requiring synthesis of multiple details."
            )
        else:
            difficulty_instructions = (
                "Create conceptual inference questions that require understanding and light reasoning."
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
- For EASY: no trick wording, no negations like "NOT", single-fact recall.
- For MEDIUM: include paraphrase/inference, not direct copy of one sentence.
- For HARD: require combining at least two ideas from different parts of the text.

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
Do not wrap JSON in markdown fences.
Do not add explanations before or after JSON.
`correct_answer` must be one of: "A", "B", "C", "D".

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
            if not isinstance(q, dict):
                continue

            question = str(
                q.get("question")
                or q.get("stem")
                or q.get("prompt")
                or q.get("query")
                or ""
            ).strip()
            options = self._normalise_options(q.get("options"))
            correct = str(
                q.get("correct_answer")
                or q.get("answer")
                or q.get("correct")
                or q.get("correct_option")
                or ""
            ).strip()

            if not question or len(options) != 4:
                continue

            # accept either "A"/"B"/"C"/"D", "1-4", or exact option text
            if correct.upper() in ("A", "B", "C", "D"):
                idx = {"A": 0, "B": 1, "C": 2, "D": 3}[correct.upper()]
            elif correct in ("1", "2", "3", "4"):
                idx = int(correct) - 1
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

    def _normalise_options(self, raw_options: Any) -> List[str]:
        if raw_options is None:
            return []

        # Format: ["a", "b", "c", "d"]
        if isinstance(raw_options, list):
            options: List[str] = []
            for item in raw_options:
                if isinstance(item, str):
                    options.append(item.strip())
                elif isinstance(item, dict):
                    # Format: [{"label":"A","text":"..."}, ...]
                    text = item.get("text") or item.get("value") or item.get("option")
                    if text:
                        options.append(str(text).strip())
            return [o for o in options if o][:4]

        # Format: {"A":"...", "B":"...", "C":"...", "D":"..."}
        if isinstance(raw_options, dict):
            letter_keys = ["A", "B", "C", "D"]
            if all(k in raw_options for k in letter_keys):
                return [str(raw_options[k]).strip() for k in letter_keys]

            # Fallback for lowercase/numbered keys
            key_order = ["a", "b", "c", "d", "1", "2", "3", "4"]
            options: List[str] = []
            for key in key_order:
                if key in raw_options:
                    options.append(str(raw_options[key]).strip())
            if len(options) >= 4:
                return options[:4]

            # Last resort: take first 4 values in dict order
            values = [str(v).strip() for v in raw_options.values() if str(v).strip()]
            return values[:4]

        return []

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

    def _build_fallback_questions(self, content: str, expected: int, difficulty: str) -> List[Dict[str, Any]]:
        """Build proper MCQ-style questions from source statements."""
        normalized = " ".join(content.split())
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
        facts = [s for s in raw_sentences if len(s.split()) >= 8 and 50 <= len(s) <= 220]
        if len(facts) < 2:
            raise RuntimeError("Unable to generate fallback quiz questions.")

        permutations = [
            [0, 1, 2, 3],  # A
            [1, 0, 2, 3],  # B
            [1, 2, 0, 3],  # C
            [1, 2, 3, 0],  # D
        ]
        diff = (difficulty or "medium").lower().strip()
        if diff not in ("easy", "medium", "hard"):
            diff = "medium"

        def topic_from_sentence(sentence: str) -> str:
            words = re.findall(r"\b[A-Za-z][A-Za-z0-9\-]{3,}\b", sentence)
            if not words:
                return "the passage"
            return " ".join(words[:3])

        def mutate_false(statement: str, variant: int) -> str:
            s = statement.rstrip(".")
            if diff == "easy":
                if variant == 0:
                    return f"The passage does not discuss this point: {s}."
                if variant == 1 and " is " in s:
                    return s.replace(" is ", " was ", 1) + "."
                return f"The passage states the opposite of this claim: {s}."
            if diff == "hard":
                if variant == 0:
                    return f"{s}. However, this ignores the broader context in the passage."
                if variant == 1:
                    return f"{s}. This conclusion conflicts with another key detail in the text."
                return f"{s}. This overstates what the passage actually supports."
            if variant == 0:
                return f"{s}. This is only partially supported by the passage."
            if variant == 1:
                return f"{s}. This misses an important condition from the text."
            return f"{s}. This interpretation is weaker than the best-supported claim."

        questions: List[Dict[str, Any]] = []
        n = len(facts)
        for idx in range(expected):
            correct = facts[idx % n]
            topic = topic_from_sentence(correct)

            if diff == "easy":
                stem = f"According to the passage, which statement about {topic} is correct?"
            elif diff == "hard":
                stem = f"Which option is best supported by the passage when evaluating claims about {topic}?"
            else:
                stem = f"Based on the passage, which claim about {topic} is most accurate?"

            distractors: List[str] = []
            for jump in range(1, n + 1):
                candidate = facts[(idx + jump) % n]
                if candidate != correct and candidate not in distractors:
                    distractors.append(candidate)
                if len(distractors) == 2:
                    break
            while len(distractors) < 2:
                distractors.append(mutate_false(correct, len(distractors)))

            distractors.append(mutate_false(correct, 2))
            base_options = [correct, distractors[0], distractors[1], distractors[2]]
            order = permutations[idx % len(permutations)]
            options = [base_options[i] for i in order]
            correct_index = order.index(0)

            questions.append(
                {
                    "question": stem,
                    "options": options,
                    "correct_answer": ["A", "B", "C", "D"][correct_index],
                }
            )

        return questions
