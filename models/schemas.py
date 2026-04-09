"""Pydantic response models for API payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobListingBase(BaseModel):
    """Shared fields returned for job listings."""

    title: str
    company: str
    location: str
    url: str
    summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


class JobListingResponse(JobListingBase):
    """Shape used by job listing collection endpoints."""

    id: int
    seen: bool
    scraped_at: datetime


class JobListingDetail(JobListingBase):
    """Detailed shape used by job listing detail endpoints."""

    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    description_snippet: str
