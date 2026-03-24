"""In-memory background correlation job tracker."""

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class CorrelationJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Module-level store — survives across requests within a single process.
_jobs: dict[str, dict[str, Any]] = {}


def create_job(total: int = 0) -> str:
    """Create a new correlation job and return its ID."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": CorrelationJobStatus.QUEUED,
        "progress": 0,
        "total": total,
        "matched": 0,
        "queued_for_review": 0,
        "errors": [],
        "started_at": None,
        "completed_at": None,
    }
    return job_id


def start_job(job_id: str, total: int | None = None) -> None:
    """Mark a job as running."""
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = CorrelationJobStatus.RUNNING
    job["started_at"] = datetime.now(timezone.utc).isoformat()
    if total is not None:
        job["total"] = total


def update_progress(
    job_id: str,
    *,
    progress: int | None = None,
    matched_delta: int = 0,
    review_delta: int = 0,
) -> None:
    """Increment job counters."""
    job = _jobs.get(job_id)
    if not job:
        return
    if progress is not None:
        job["progress"] = progress
    job["matched"] += matched_delta
    job["queued_for_review"] += review_delta


def complete_job(job_id: str) -> None:
    """Mark a job as completed."""
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = CorrelationJobStatus.COMPLETED
    job["completed_at"] = datetime.now(timezone.utc).isoformat()


def fail_job(job_id: str, error: str) -> None:
    """Mark a job as failed."""
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = CorrelationJobStatus.FAILED
    job["errors"].append(error)
    job["completed_at"] = datetime.now(timezone.utc).isoformat()


def add_error(job_id: str, error: str) -> None:
    """Append an error without failing the whole job."""
    job = _jobs.get(job_id)
    if job:
        job["errors"].append(error)


def get_job_status(job_id: str) -> dict[str, Any] | None:
    """Return the current state of a job, or None if unknown."""
    return _jobs.get(job_id)
