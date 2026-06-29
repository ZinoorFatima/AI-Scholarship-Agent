"""The orchestrator runs all six stages and persists the run (agents stubbed)."""
import scholar.orchestrator as o
from scholar import store
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
)

APPLICANT = Applicant(cv="cv", transcript="t", achievements="a", target_scholarship="s")


def test_run_pipeline_fills_all_stages_and_persists(tmp_path, monkeypatch):
    # Persist runs under a temp dir.
    monkeypatch.setattr(store.get_settings(), "runs_dir", str(tmp_path))

    monkeypatch.setattr(o, "check_eligibility",
        lambda a: Eligibility(eligible=True, criteria=[EligibilityCriterion(requirement="r", met=True, evidence="e")], summary="ok"))
    monkeypatch.setattr(o, "build_profile",
        lambda a: Profile(academic_strengths=["x"], research_experience=[], projects=[], leadership_activities=[], awards=[], summary="s"))
    monkeypatch.setattr(o, "analyze_gaps",
        lambda p, s: GapAnalysis(strengths=["a"], weaknesses=["b"], recommendations=["c"]))
    monkeypatch.setattr(o, "draft_essays",
        lambda p, g, s: EssaySet(essays=[Essay(title="PS", prompt="goals", content="...")]))
    monkeypatch.setattr(o, "review_essays",
        lambda e: Review(scores=[EssayScore(essay_title="PS", leadership=8, impact=7, clarity=9, recommendations=[])], overall_feedback="good"))
    monkeypatch.setattr(o, "assess_readiness",
        lambda a, e: Readiness(checklist=[ChecklistItem(item="CV", complete=True, note="")], ready_to_submit=True, summary="ready"))

    state = o.run_pipeline(APPLICANT, run_id="testrun")

    # Every stage populated.
    assert state.eligibility.eligible is True
    assert state.profile.summary == "s"
    assert state.gaps.weaknesses == ["b"]
    assert len(state.essays.essays) == 1
    assert state.review.scores[0].clarity == 9
    assert state.readiness.ready_to_submit is True

    # Persisted and reloadable.
    reloaded = store.load("testrun")
    assert reloaded == state
