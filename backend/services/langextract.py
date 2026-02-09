"""
Local, open-source text extraction utility used by the app.

This module intentionally exposes a simple `LangExtract` interface so the
rest of the codebase can treat it as the text-extraction component.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import PyPDF2
import requests
from bs4 import BeautifulSoup


SourceType = Literal["pdf", "url", "text"]


@dataclass
class ExtractResult:
    text: str
    source_type: SourceType
    source_label: str | None = None


class LangExtract:
    """Minimal LangExtract-style API for PDFs and URLs."""

    @staticmethod
    def from_pdf(path: str, label: str | None = None) -> ExtractResult:
        text_parts: list[str] = []
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
        except Exception as exc:  # pragma: no cover - simple pass-through
            raise ValueError(f"Failed to extract PDF text: {exc}") from exc

        text = "\n".join(t for t in text_parts if t).strip()
        if not text:
            raise ValueError("No text extracted from PDF.")

        return ExtractResult(text=text, source_type="pdf", source_label=label)

    @staticmethod
    def from_url(url: str) -> ExtractResult:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors
            raise ValueError(f"Failed to fetch URL: {exc}") from exc

        soup = BeautifulSoup(resp.content, "html.parser")

        # remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        raw = soup.get_text(separator="\n")
        # normalise whitespace
        lines = [line.strip() for line in raw.splitlines()]
        text = "\n".join(line for line in lines if line).strip()

        if not text:
            raise ValueError("No text extracted from URL.")

        return ExtractResult(text=text, source_type="url", source_label=url)

