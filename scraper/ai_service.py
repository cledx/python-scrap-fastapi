"""AI enrichment service for job listings."""

from __future__ import annotations

import json
import os
from pathlib import Path

from litellm import acompletion

GITHUB_MODELS_API_BASE = "https://models.inference.ai.azure.com"
GITHUB_MODELS_MODEL = os.getenv("GITHUB_MODELS_MODEL", "github/gpt-4o-mini")


def _load_resume_context() -> str:
    resume_path = Path(__file__).resolve().parent.parent / "resume.md"
    try:
        return resume_path.read_text(encoding="utf-8")
    except OSError:
        return ""


RESUME_CONTEXT = _load_resume_context()


def _extract_json_block(raw_text: str) -> str:
    """Extract JSON payload if response is wrapped in markdown code fences."""
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


async def enrich_listing(description: str) -> dict:
    """Enrich a job description using resume context and return parsed JSON."""
    prompt = f"""You are an assistant that evaluates job listings against a candidate resume.
    The pros and cons should be based on whether the job listing is a good fit for the candidate based on the resume.
    The summary should end with an indication on the likelihood of the candidate getting the job based on the job listing and resume.

Resume context:
{RESUME_CONTEXT}

Job description:
{description}

Return only valid JSON with exactly these keys:
- "summary": string
- "pros": list[string]
- "cons": list[string]
"""

    response = await acompletion(
        model=GITHUB_MODELS_MODEL,
        api_base=GITHUB_MODELS_API_BASE,
        api_key=os.getenv("GITHUB_TOKEN"),
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content or "{}"
    json_text = _extract_json_block(raw_content)
    try:
        parsed = json.loads(json_text)
    except (json.JSONDecodeError, TypeError):
        return {"summary": "", "pros": [], "cons": []}

    if not isinstance(parsed, dict):
        return {"summary": "", "pros": [], "cons": []}

    return {
        "summary": str(parsed.get("summary", "")),
        "pros": [str(item) for item in parsed.get("pros", []) if isinstance(item, str)],
        "cons": [str(item) for item in parsed.get("cons", []) if isinstance(item, str)],
    }
