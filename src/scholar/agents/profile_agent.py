"""Profile Analysis Agent — extracts a structured candidate profile."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import Applicant, Profile

SYSTEM = """\
You are an admissions analyst building a candidate profile.

From the applicant's CV, transcript, and achievements, extract a structured
profile. Rules:
- Sort concrete facts into: academic strengths, research experience, projects,
  leadership activities, awards.
- Be specific — name the project, the role, the award, the GPA — don't write
  vague generalities.
- Only include what the materials support; do not invent credentials.
- The summary is a 2-3 sentence positioning statement for this candidate.\
"""


def build_profile(
    applicant: Applicant, *, client: genai.Client | None = None
) -> Profile:
    settings = get_settings()
    prompt = (
        "CV:\n"
        f"{applicant.cv}\n\n"
        "TRANSCRIPT:\n"
        f"{applicant.transcript}\n\n"
        "ACHIEVEMENTS:\n"
        f"{applicant.achievements}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=Profile,
        model=settings.default_model,
        client=client,
    )
