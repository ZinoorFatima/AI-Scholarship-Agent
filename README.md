# AI Scholarship Agent

Turns an applicant's materials into a full application workup: an eligibility
check, a structured profile, a gap analysis, drafted essays, a rubric review,
and a submission checklist. Six cooperating agents, typed Pydantic contracts
between stages, runs persisted to disk.

```
Applicant materials
   │
   ▼  Eligibility ─→ Profile ─→ Gap analysis ─→ Essay drafting ─→ Review ─→ Readiness
   (CV, transcript, achievements, target scholarship)
```

Backend: **FastAPI + Google Gemini** (`google-genai`). Frontend: a thin
single-page web app served by the same server.

## Features

- **Find scholarships** — free-text search, grounded with Google Search so
  results are real and current (name, provider, amount, deadline, official link).
- **Recommend from your CV** — paste/upload a CV and get matched scholarships
  with a per-result explanation of *why* it fits.
- **File upload** — drop in a CV or transcript as **PDF / DOCX / TXT**; the
  backend extracts the text for you.
- **Full application workup** — the six-agent pipeline below.

## Why it's interesting

- **Multi-agent orchestration** — six specialised agents behind one orchestrator.
- **Structured outputs** — every stage emits a validated Pydantic object (via
  Gemini's `response_schema` / `response.parsed`), so the data flowing between
  agents is typed, not hoped-for.
- **Grounded retrieval** — search & recommendations use Gemini's Google-Search
  grounding for real, current scholarships (with a non-grounded fallback).
- **Document intelligence** — reads CV/transcript files, extracts a candidate
  profile, and matches it against a scholarship's real requirements.
- **Persisted runs** — each run is saved to `runs/<id>/state.json`.

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate     | macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # then fill in GEMINI_API_KEY
```

`GEMINI_API_KEY` is the only credential needed — get one free at
https://aistudio.google.com/apikey.

## Run it

### Web app (backend + frontend)

```bash
uvicorn scholar.api:app --reload
# open http://127.0.0.1:8000
```

Workflow: **search** (or **recommend from CV**) → click *Use for application* →
**upload** your CV/transcript or paste them → **Analyze**. The six agents run in
sequence and the page renders each result.

### API endpoints

| Method & path | Purpose |
|---|---|
| `POST /api/search-scholarships` | `{query}` → matching scholarships (grounded) |
| `POST /api/recommend-scholarships` | `{cv}` → recommended scholarships (grounded) |
| `POST /api/extract` | multipart file (PDF/DOCX/TXT) → extracted text |
| `POST /api/analyze` | applicant materials → full 6-stage run |
| `GET /api/runs/{id}` | fetch a persisted run |

### CLI

```bash
scholar --cv cv.txt --transcript transcript.txt \
        --achievements achievements.txt --scholarship scholarship.txt
```

Each argument accepts either a path to a `.txt` file or the raw text. Add
`--json` to print the full structured run. Artifacts land in `runs/<id>/`.

## Test

```bash
pytest
```

Tests mock the LLM — they run offline and need no API key.

## Layout

| Path | What |
|------|------|
| `src/scholar/schemas.py` | Typed contracts for every stage + `RunState` |
| `src/scholar/llm.py` | `generate_structured()` — schema-constrained Gemini calls |
| `src/scholar/agents/` | The six agents |
| `src/scholar/discovery.py` | Grounded scholarship search & recommendations |
| `src/scholar/extract.py` | CV/transcript file → text (PDF/DOCX/TXT) |
| `src/scholar/orchestrator.py` | Pipeline + CLI |
| `src/scholar/api.py` | FastAPI backend |
| `web/` | Thin single-page frontend |

## Notes / roadmap

Materials are handled as text (uploaded files are converted to text on the
backend). Image-only/scanned PDFs need OCR (not included). Multi-scholarship
comparison and reference-letter drafting are natural next steps.
