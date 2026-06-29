"""Scholarship discovery parses grounded JSON and requests the search tool."""
from types import SimpleNamespace

from scholar.discovery import recommend_scholarships, search_scholarships


class FakeGroundedClient:
    """Returns a `.text` JSON payload (mimics a grounded Gemini response)."""

    def __init__(self, text):
        self._text = text
        self.calls = []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text=self._text)


PAYLOAD = """```json
{"scholarships": [
  {"name": "Global STEM Leaders", "provider": "ACME", "description": "For STEM undergrads",
   "eligibility": "CGPA>3.0", "amount": "$10,000", "deadline": "2026-09-01",
   "url": "https://example.org/stem", "fit_reason": null}
]}
```"""


def test_search_parses_grounded_json_and_uses_search_tool():
    client = FakeGroundedClient(PAYLOAD)
    res = search_scholarships("STEM scholarships", client=client)
    assert len(res.scholarships) == 1
    s = res.scholarships[0]
    assert s.name == "Global STEM Leaders"
    assert s.amount == "$10,000"
    # The Google Search tool was attached to the request.
    assert client.calls[0]["config"].tools


def test_recommend_includes_cv_and_returns_results():
    client = FakeGroundedClient(PAYLOAD)
    res = recommend_scholarships("BSc CS, GPA 3.8, robotics club president", client=client)
    assert res.scholarships[0].provider == "ACME"
    assert "robotics" in client.calls[0]["contents"]
