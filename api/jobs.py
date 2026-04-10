"""Job listing API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from models.database import get_session
from models.job_listing import JobListing
from models.schemas import JobListingResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobListingResponse])
def list_jobs(
    seen: Optional[bool] = None,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[JobListingResponse]:
    """Return paginated job listings with optional seen filter."""

    statement = select(JobListing)
    if seen is not None:
        statement = statement.where(JobListing.seen == seen)

    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement))


@router.patch("/jobs/{job_id}/seen", response_model=JobListingResponse)
def mark_job_seen(job_id: int, session: Session = Depends(get_session)) -> JobListingResponse:
    """Mark a job listing as seen."""

    statement = select(JobListing).where(JobListing.id == job_id)
    listing = session.exec(statement).first()
    if listing is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    listing.seen = True
    session.add(listing)
    session.commit()
    session.refresh(listing)
    return listing
