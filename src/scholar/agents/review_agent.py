"""Review Agent — scores the drafted essays against a rubric."""
from __future__ import annotations

from google import genai

from ..config import get_settings
from ..llm import generate_structured
from ..schemas import EssaySet, Review

SYSTEM = """\
You are a scholarship selection committee member scoring essays.

Score EACH essay on three rubric dimensions, integers from 0 to 10:
- leadership: evidence of initiative, influence, and responsibility.
- impact: tangible difference made, with scale and outcomes.
- clarity: structure, focus, and quality of writing.

Rules:
- Score honestly and consistently against the rubric — a 10 is exceptional.
- For each essay, give specific, actionable recommendations to raise the weakest
  dimension.
- overall_feedback summarises themes across all essays and the single highest-
  leverage improvement.\
"""


def review_essays(
    essays: EssaySet, *, client: genai.Client | None = None
) -> Review:
    settings = get_settings()
    prompt = (
        "Score the following essays against the rubric.\n\n"
        f"{essays.model_dump_json(indent=2)}"
    )
    return generate_structured(
        system=SYSTEM,
        prompt=prompt,
        schema=Review,
        model=settings.default_model,
        client=client,
    )
