"""Job listing row stored in the database."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class JobListing(SQLModel, table=True):
    """A scraped job posting and optional AI-enriched fields."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    location: str
    url: str
    url_hash: str = Field(unique=True)
    description_snippet: str
    summary: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    seen: bool = Field(default=False)
    posted_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
