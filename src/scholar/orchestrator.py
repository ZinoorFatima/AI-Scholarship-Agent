"""Pipeline orchestration for the scholarship agent.

Runs the six agents in sequence, persisting the run after each stage so a run
can be inspected by ``run_id``. Both the CLI (``main``) and the FastAPI service
call :func:`run_pipeline`.
"""
from __future__ import annotations

import argparse
import sys
import uuid

from . import store
from .agents import (
    analyze_gaps,
    assess_readiness,
    build_profile,
    check_eligibility,
    draft_essays,
    review_essays,
)
from .schemas import Applicant, RunState


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def run_pipeline(applicant: Applicant, *, run_id: str | None = None,
                 verbose: bool = False) -> RunState:
    """Run all six stages end to end, persisting after each."""
    state = RunState(run_id=run_id or new_run_id(), applicant=applicant)

    def step(label: str) -> None:
        if verbose:
            print(label, flush=True)

    step("[1/6] Checking eligibility...")
    state.eligibility = check_eligibility(applicant)
    store.save(state)

    step("[2/6] Building candidate profile...")
    state.profile = build_profile(applicant)
    store.save(state)

    step("[3/6] Analysing gaps...")
    state.gaps = analyze_gaps(state.profile, applicant.target_scholarship)
    store.save(state)

    step("[4/6] Drafting essays...")
    state.essays = draft_essays(state.profile, state.gaps, applicant.target_scholarship)
    store.save(state)

    step("[5/6] Reviewing essays...")
    state.review = review_essays(state.essays)
    store.save(state)

    step("[6/6] Assessing submission readiness...")
    state.readiness = assess_readiness(applicant, state.essays)
    store.save(state)

    return state


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _read(path_or_text: str) -> str:
    """If the argument is a path to an existing file, read it; else treat as text."""
    from pathlib import Path

    p = Path(path_or_text)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return path_or_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scholar",
        description="AI Scholarship Agent: materials -> eligibility, profile, "
        "gaps, essays, review, and a submission checklist.",
    )
    parser.add_argument("--cv", required=True, help="CV text or path to a .txt file.")
    parser.add_argument("--transcript", required=True, help="Transcript text or path.")
    parser.add_argument("--achievements", required=True, help="Achievements text or path.")
    parser.add_argument("--scholarship", required=True, help="Scholarship requirements text or path.")
    parser.add_argument("--json", action="store_true", help="Print full run state as JSON.")
    args = parser.parse_args(argv)

    applicant = Applicant(
        cv=_read(args.cv),
        transcript=_read(args.transcript),
        achievements=_read(args.achievements),
        target_scholarship=_read(args.scholarship),
    )
    try:
        state = run_pipeline(applicant, verbose=True)
    except Exception as exc:  # clean message, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(state.model_dump_json(indent=2))
    else:
        elig = "ELIGIBLE" if state.eligibility.eligible else "NOT ELIGIBLE"
        print(f"\nEligibility: {elig} — {state.eligibility.summary}")
        print(f"Essays drafted: {len(state.essays.essays)}")
        ready = "READY" if state.readiness.ready_to_submit else "NOT READY"
        print(f"Submission: {ready} — {state.readiness.summary}")
    print(f"\nRun saved: {state.run_id}  (runs/{state.run_id}/state.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
