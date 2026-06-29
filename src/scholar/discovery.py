"""Scholarship discovery: free-text search and CV-based recommendations.

Both use Google-Search-grounded generation so results reflect real, currently
listed scholarships rather than only the model's training data.
"""
from __future__ import annotations

from google import genai

from .config import get_settings
from .llm import generate_grounded
from .schemas import ScholarshipResults

SEARCH_SYSTEM = """\
You are a scholarship search assistant.

Use web search to find REAL, currently-listed scholarships matching the user's
query. For each result, capture the name, provider, a one-line description, who
is eligible, the award amount, the deadline, and the official URL. Only include
scholarships you can actually find — never invent names, links, or deadlines.
If a field is unknown, set it to null.\
"""

RECOMMEND_SYSTEM = """\
You are a scholarship matching assistant.

Given a candidate's CV, use web search to find REAL scholarships they are a
strong fit for. Consider their field of study, level, achievements, location,
and background. For each recommendation, fill 'fit_reason' with a specific,
honest explanation of why this candidate matches. Never invent scholarships,
links, or deadlines; set unknown fields to null.\
"""


def search_scholarships(
    query: str, *, client: genai.Client | None = None
) -> ScholarshipResults:
    """Find scholarships matching a free-text query."""
    settings = get_settings()
    prompt = (
        f"Find up to 8 real, currently-open scholarships matching this query:\n"
        f"{query}"
    )
    return generate_grounded(
        system=SEARCH_SYSTEM,
        prompt=prompt,
        schema=ScholarshipResults,
        model=settings.default_model,
        client=client,
    )


def recommend_scholarships(
    cv: str, *, client: genai.Client | None = None
) -> ScholarshipResults:
    """Recommend scholarships that fit a candidate's CV."""
    settings = get_settings()
    prompt = (
        "Based on the following CV, recommend up to 8 real scholarships this "
        "person is a strong fit for. Explain the fit in 'fit_reason'.\n\nCV:\n"
        f"{cv}"
    )
    return generate_grounded(
        system=RECOMMEND_SYSTEM,
        prompt=prompt,
        schema=ScholarshipResults,
        model=settings.default_model,
        client=client,
    )
