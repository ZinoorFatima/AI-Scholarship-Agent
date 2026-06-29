"""Eligibility Agent — checks the applicant against the scholarship's rules."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import Applicant, Eligibility

SYSTEM = """\
You are a scholarship eligibility officer.

Read the scholarship's stated requirements, then check the applicant's CV,
transcript, and achievements against EACH requirement. Rules:
- Extract every concrete requirement (e.g. minimum CGPA, leadership experience,
  community impact, nationality, field of study, enrolment status).
- For each, decide met/not-met and cite the specific evidence from the
  applicant's materials — or state exactly what is missing.
- Be strict and honest: do not mark a requirement met without evidence.
- 'eligible' is true only if every hard requirement is met.
- The summary should tell the applicant where they stand in one or two sentences.\
"""


def check_eligibility(
    applicant: Applicant, *, client: genai.Client | None = None
) -> Eligibility:
    settings = get_settings()
    prompt = (
        "SCHOLARSHIP REQUIREMENTS:\n"
        f"{applicant.target_scholarship}\n\n"
        "APPLICANT CV:\n"
        f"{applicant.cv}\n\n"
        "TRANSCRIPT:\n"
        f"{applicant.transcript}\n\n"
        "ACHIEVEMENTS:\n"
        f"{applicant.achievements}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=Eligibility,
        model=settings.default_model,
        client=client,
    )
