"""Essay Drafting Agent — drafts the personal statement and scholarship essays."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import EssaySet, GapAnalysis, Profile

SYSTEM = """\
You are an expert scholarship essay writer.

Draft a set of essays for this candidate and scholarship. Always include:
- A "Personal Statement" covering career goals, motivation, and intended impact.
- Essays for the scholarship's themes (commonly: Leadership, STEM/field
  contribution, Future vision). Adapt to whatever this scholarship emphasises.

Rules:
- Write in the candidate's voice, grounded in their REAL profile — use their
  actual projects, roles, and awards. Never fabricate experiences.
- Where the gap analysis flags a weakness, address it honestly and frame growth
  positively rather than hiding it.
- Each essay should be substantive (roughly 250-400 words), specific, and
  compelling — concrete stories over generic claims.
- Set 'prompt' to the theme each essay answers.\
"""


def draft_essays(
    profile: Profile,
    gaps: GapAnalysis,
    target_scholarship: str,
    *,
    client: genai.Client | None = None,
) -> EssaySet:
    settings = get_settings()
    prompt = (
        "SCHOLARSHIP:\n"
        f"{target_scholarship}\n\n"
        "CANDIDATE PROFILE:\n"
        f"{profile.model_dump_json(indent=2)}\n\n"
        "GAP ANALYSIS:\n"
        f"{gaps.model_dump_json(indent=2)}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=EssaySet,
        model=settings.essay_model,
        client=client,
    )
