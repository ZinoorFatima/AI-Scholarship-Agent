"""Each agent produces a validated object against a mocked Gemini client."""
from types import SimpleNamespace

from scholar.agents import (
    analyze_gaps,
    assess_readiness,
    build_profile,
    check_eligibility,
    draft_essays,
    review_essays,
)
from scholar.schemas import (
    Applicant,
    Eligibility,
    EligibilityCriterion,
    Essay,
    EssayScore,
    EssaySet,
    GapAnalysis,
    Profile,
    Readiness,
    ChecklistItem,
    Review,
)


class FakeClient:
    """Stands in for genai.Client; returns a canned `.parsed` response."""

    def __init__(self, output):
        self._output = output
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(parsed=self._output)


APPLICANT = Applicant(
    cv="BSc CS, 3.7 GPA", transcript="GPA 3.7", achievements="Robotics club president",
    target_scholarship="STEM scholarship, CGPA>3.0, leadership required",
)
PROFILE = Profile(
    academic_strengths=["CS"], research_experience=[], projects=["robot"],
    leadership_activities=["club president"], awards=[], summary="strong STEM",
)


def test_eligibility():
    out = Eligibility(eligible=True, criteria=[EligibilityCriterion(requirement="CGPA>3", met=True, evidence="3.7")], summary="ok")
    client = FakeClient(out)
    assert check_eligibility(APPLICANT, client=client) is out
    sent = client.calls[0]["contents"]
    assert "STEM scholarship" in sent and "3.7" in sent


def test_profile():
    client = FakeClient(PROFILE)
    assert build_profile(APPLICANT, client=client) is PROFILE


def test_gaps_includes_scholarship_and_profile():
    out = GapAnalysis(strengths=["x"], weaknesses=["y"], recommendations=["z"])
    client = FakeClient(out)
    assert analyze_gaps(PROFILE, "STEM scholarship priorities", client=client) is out
    sent = client.calls[0]["contents"]
    assert "STEM scholarship priorities" in sent and "strong STEM" in sent


def test_essays():
    out = EssaySet(essays=[Essay(title="Personal Statement", prompt="goals", content="...")])
    client = FakeClient(out)
    gaps = GapAnalysis(strengths=[], weaknesses=[], recommendations=[])
    assert draft_essays(PROFILE, gaps, "scholarship", client=client) is out


def test_review():
    out = Review(scores=[EssayScore(essay_title="PS", leadership=8, impact=6, clarity=9, recommendations=[])], overall_feedback="ok")
    client = FakeClient(out)
    essays = EssaySet(essays=[Essay(title="PS", prompt="p", content="c")])
    assert review_essays(essays, client=client) is out


def test_readiness():
    out = Readiness(checklist=[ChecklistItem(item="CV", complete=True, note="")], ready_to_submit=False, summary="almost")
    client = FakeClient(out)
    essays = EssaySet(essays=[Essay(title="PS", prompt="p", content="c")])
    assert assess_readiness(APPLICANT, essays, client=client) is out
