"""Submission Readiness Agent — final pre-submission checklist."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import Applicant, EssaySet, Readiness

SYSTEM = """\
You are a submission coordinator running the final pre-submission check.

Produce a submission checklist for this application. Rules:
- Cover the essentials: CV provided, transcript provided, each required essay
  drafted, essays within any stated word limits, references/recommendation
  letters, and any scholarship-specific documents named in the requirements.
- Mark each item complete only if the evidence supports it; otherwise note
  exactly what the applicant still needs to do.
- 'ready_to_submit' is true only when every required item is complete.
- Keep the summary to a clear go / not-yet verdict with the top blockers.\
"""


def assess_readiness(
    applicant: Applicant,
    essays: EssaySet,
    *,
    client: genai.Client | None = None,
) -> Readiness:
    settings = get_settings()
    prompt = (
        "SCHOLARSHIP REQUIREMENTS:\n"
        f"{applicant.target_scholarship}\n\n"
        "PROVIDED CV (present if non-empty):\n"
        f"{applicant.cv[:500]}\n\n"
        "PROVIDED TRANSCRIPT (present if non-empty):\n"
        f"{applicant.transcript[:500]}\n\n"
        "DRAFTED ESSAYS:\n"
        f"{essays.model_dump_json(indent=2)}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=Readiness,
        model=settings.default_model,
        client=client,
    )
