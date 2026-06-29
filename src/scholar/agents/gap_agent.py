"""Gap Analysis Agent — strengths vs weaknesses against the scholarship."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import GapAnalysis, Profile

SYSTEM = """\
You are a scholarship coach doing a gap analysis.

Given a candidate profile and the scholarship's priorities, identify where the
candidate is strong and where they are weak RELATIVE TO WHAT THIS SCHOLARSHIP
REWARDS. Rules:
- Strengths and weaknesses must be judged against the scholarship's emphasis
  (e.g. if it prizes community impact, weak community work is a real gap).
- Recommendations must be concrete and actionable before the deadline (e.g.
  "secure a recommendation letter from your research supervisor"), not generic
  advice.
- Be candid — the value here is an honest assessment, not flattery.\
"""


def analyze_gaps(
    profile: Profile,
    target_scholarship: str,
    *,
    client: genai.Client | None = None,
) -> GapAnalysis:
    settings = get_settings()
    prompt = (
        "SCHOLARSHIP PRIORITIES:\n"
        f"{target_scholarship}\n\n"
        "CANDIDATE PROFILE:\n"
        f"{profile.model_dump_json(indent=2)}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=GapAnalysis,
        model=settings.default_model,
        client=client,
    )
