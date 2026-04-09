"""Job listing SQLModel models and API schemas."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class JobListingBase(SQLModel):
    """Fields shared across DB and API job listing models."""

    title: str
    company: str
    location: str
    url: str
    description_snippet: str
    summary: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    seen: bool = False
    posted_at: Optional[datetime] = None


class JobListing(JobListingBase, table=True):
    """Database table model for a scraped job posting."""

    id: Optional[int] = Field(default=None, primary_key=True)
    url_hash: str = Field(unique=True)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class JobListingResponse(JobListingBase):
    """API response schema for a job listing."""

    id: int
    scraped_at: datetime
