"""Schemas validate and round-trip through JSON."""
from scholar.schemas import (
    Applicant,
    ChecklistItem,
    Eligibility,
    EligibilityCriterion,
    Essay,
    EssayScore,
    EssaySet,
    GapAnalysis,
    Profile,
    Readiness,
    Review,
    RunState,
)


def test_applicant_roundtrip():
    a = Applicant(cv="cv", transcript="t", achievements="a", target_scholarship="s")
    assert Applicant.model_validate_json(a.model_dump_json()) == a


def test_full_runstate_roundtrip():
    state = RunState(
        run_id="abc123",
        applicant=Applicant(cv="cv", transcript="t", achievements="a", target_scholarship="s"),
        eligibility=Eligibility(
            eligible=True,
            criteria=[EligibilityCriterion(requirement="CGPA>3", met=True, evidence="3.7")],
            summary="ok",
        ),
        profile=Profile(
            academic_strengths=["math"], research_experience=[], projects=["x"],
            leadership_activities=["club lead"], awards=["dean's list"], summary="strong",
        ),
        gaps=GapAnalysis(strengths=["academics"], weaknesses=["community"], recommendations=["volunteer"]),
        essays=EssaySet(essays=[Essay(title="Personal Statement", prompt="goals", content="...")]),
        review=Review(
            scores=[EssayScore(essay_title="Personal Statement", leadership=8, impact=6, clarity=9, recommendations=["add metrics"])],
            overall_feedback="solid",
        ),
        readiness=Readiness(
            checklist=[ChecklistItem(item="References", complete=False, note="add 2 letters")],
            ready_to_submit=False, summary="almost",
        ),
    )
    restored = RunState.model_validate_json(state.model_dump_json())
    assert restored == state
    assert restored.review.scores[0].leadership == 8
