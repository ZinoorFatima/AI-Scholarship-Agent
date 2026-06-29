"""Typed contracts for the scholarship pipeline.

Each agent consumes earlier stages' outputs and produces the next. Models avoid
numeric/length constraints (min/max) to stay portable across structured-output
schema compilers (e.g. Gemini's ``response_schema``); ranges are enforced via
the prompts instead.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Stage 0 — applicant inputs
# --------------------------------------------------------------------------- #
class Applicant(BaseModel):
    """The raw materials an applicant provides (as text)."""

    cv: str = Field(description="The applicant's CV / resume, as text.")
    transcript: str = Field(description="Academic transcript or grade summary.")
    achievements: str = Field(
        description="Awards, leadership roles, community work, projects."
    )
    target_scholarship: str = Field(
        description="The scholarship's description and eligibility requirements."
    )


# --------------------------------------------------------------------------- #
# Discovery — search results & CV-based recommendations
# --------------------------------------------------------------------------- #
class Scholarship(BaseModel):
    name: str = Field(description="Scholarship name.")
    provider: str | None = Field(default=None, description="Sponsoring organisation.")
    description: str | None = Field(default=None, description="What it is, in brief.")
    eligibility: str | None = Field(default=None, description="Who can apply.")
    amount: str | None = Field(default=None, description="Award value, if known.")
    deadline: str | None = Field(default=None, description="Application deadline, if known.")
    url: str | None = Field(default=None, description="Official link, if known.")
    fit_reason: str | None = Field(
        default=None, description="Why this fits the applicant (recommendations only)."
    )


class ScholarshipResults(BaseModel):
    scholarships: list[Scholarship] = Field(description="The matched scholarships.")


# --------------------------------------------------------------------------- #
# Stage 1 — Eligibility
# --------------------------------------------------------------------------- #
class EligibilityCriterion(BaseModel):
    requirement: str = Field(description="A single stated requirement.")
    met: bool = Field(description="Whether the applicant meets it.")
    evidence: str = Field(description="The evidence (or what's missing).")


class Eligibility(BaseModel):
    eligible: bool = Field(description="Overall: does the applicant qualify?")
    criteria: list[EligibilityCriterion] = Field(
        description="Per-requirement assessment."
    )
    summary: str = Field(description="A short verdict the applicant can act on.")


# --------------------------------------------------------------------------- #
# Stage 2 — Profile
# --------------------------------------------------------------------------- #
class Profile(BaseModel):
    """A structured candidate profile extracted from the materials."""

    academic_strengths: list[str] = Field(description="Academic strengths.")
    research_experience: list[str] = Field(description="Research experience.")
    projects: list[str] = Field(description="Notable projects.")
    leadership_activities: list[str] = Field(description="Leadership activities.")
    awards: list[str] = Field(description="Awards and honours.")
    summary: str = Field(description="A 2-3 sentence positioning summary.")


# --------------------------------------------------------------------------- #
# Stage 3 — Gap analysis
# --------------------------------------------------------------------------- #
class GapAnalysis(BaseModel):
    strengths: list[str] = Field(description="Areas where the candidate is strong.")
    weaknesses: list[str] = Field(
        description="Areas that are weak relative to the scholarship's priorities."
    )
    recommendations: list[str] = Field(
        description="Concrete actions to strengthen the application."
    )


# --------------------------------------------------------------------------- #
# Stage 4 — Essays
# --------------------------------------------------------------------------- #
class Essay(BaseModel):
    title: str = Field(description="Essay title, e.g. 'Personal Statement'.")
    prompt: str = Field(description="The question / theme this essay addresses.")
    content: str = Field(description="The drafted essay text.")


class EssaySet(BaseModel):
    essays: list[Essay] = Field(description="The drafted essays.")


# --------------------------------------------------------------------------- #
# Stage 5 — Review (scores essays against a rubric)
# --------------------------------------------------------------------------- #
class EssayScore(BaseModel):
    essay_title: str = Field(description="Which essay this scores.")
    leadership: int = Field(description="Leadership score, 0-10.")
    impact: int = Field(description="Impact score, 0-10.")
    clarity: int = Field(description="Clarity score, 0-10.")
    recommendations: list[str] = Field(description="How to improve this essay.")


class Review(BaseModel):
    scores: list[EssayScore] = Field(description="Per-essay rubric scores.")
    overall_feedback: str = Field(description="Cross-cutting feedback.")


# --------------------------------------------------------------------------- #
# Stage 6 — Submission readiness
# --------------------------------------------------------------------------- #
class ChecklistItem(BaseModel):
    item: str = Field(description="The checklist item.")
    complete: bool = Field(description="Whether it's satisfied.")
    note: str = Field(description="What's needed if incomplete.")


class Readiness(BaseModel):
    checklist: list[ChecklistItem] = Field(description="Submission checklist.")
    ready_to_submit: bool = Field(description="Is the application ready to submit?")
    summary: str = Field(description="Final go/no-go summary.")


# --------------------------------------------------------------------------- #
# Run state — persisted to disk
# --------------------------------------------------------------------------- #
class RunState(BaseModel):
    """The full state of one application run."""

    run_id: str
    applicant: Applicant
    eligibility: Eligibility | None = None
    profile: Profile | None = None
    gaps: GapAnalysis | None = None
    essays: EssaySet | None = None
    review: Review | None = None
    readiness: Readiness | None = None
