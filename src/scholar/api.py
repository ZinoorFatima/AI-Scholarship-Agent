"""FastAPI backend exposing the scholarship pipeline + serving the web frontend.

    POST /api/analyze                 applicant materials -> full run (6 stages)
    GET  /api/runs/{id}               fetch a persisted run
    POST /api/extract                 upload a CV/transcript file -> extracted text
    POST /api/search-scholarships     free-text query -> matching scholarships
    POST /api/recommend-scholarships  CV text -> recommended scholarships
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import discovery, extract, orchestrator, store
from .schemas import Applicant, RunState, ScholarshipResults

app = FastAPI(title="AI Scholarship Agent")

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

# Cap uploads at 10 MB to avoid loading huge files into memory.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


# --- request bodies -------------------------------------------------------- #
class SearchRequest(BaseModel):
    query: str


class RecommendRequest(BaseModel):
    cv: str


# --- pipeline -------------------------------------------------------------- #
@app.post("/api/analyze", response_model=RunState)
def analyze(applicant: Applicant) -> RunState:
    try:
        return orchestrator.run_pipeline(applicant)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/runs/{run_id}", response_model=RunState)
def get_run(run_id: str) -> RunState:
    try:
        return store.load(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown run {run_id!r}")


# --- file upload ----------------------------------------------------------- #
@app.post("/api/extract")
async def extract_file(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")
    try:
        text = extract.extract_text(file.filename or "", data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # malformed/corrupt file
        raise HTTPException(
            status_code=422, detail=f"Could not read {file.filename!r}: {exc}"
        )
    if not text:
        raise HTTPException(
            status_code=422,
            detail="No text found — is this a scanned/image-only PDF?",
        )
    return {"filename": file.filename, "text": text}


# --- discovery ------------------------------------------------------------- #
@app.post("/api/search-scholarships", response_model=ScholarshipResults)
def search_scholarships(body: SearchRequest) -> ScholarshipResults:
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Search query is empty.")
    try:
        return discovery.search_scholarships(body.query)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/recommend-scholarships", response_model=ScholarshipResults)
def recommend_scholarships(body: RecommendRequest) -> ScholarshipResults:
    if not body.cv.strip():
        raise HTTPException(
            status_code=400, detail="Add your CV first to get recommendations."
        )
    try:
        return discovery.recommend_scholarships(body.cv)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- static frontend ------------------------------------------------------- #
@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
