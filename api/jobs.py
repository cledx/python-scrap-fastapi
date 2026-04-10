"""Job listing API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
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
