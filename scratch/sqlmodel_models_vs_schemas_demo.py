"""Scratch demo: SQLModel table models vs non-table schemas.

Run:
    python scratch/sqlmodel_models_vs_schemas_demo.py
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class JobListingBase(SQLModel):
    """Fields shared by both DB model and API schema."""

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
    """Database table model.

    table=True tells SQLModel to map this class to a SQLAlchemy table.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    url_hash: str = Field(unique=True, index=True)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class JobListingResponse(JobListingBase):
    """API response schema.

    No table=True means this is a Pydantic-style data schema only.
    """

    id: int
    scraped_at: datetime


def main() -> None:
    # 1) Base schema instance (shared fields only)
    base = JobListingBase(
        title="Backend Engineer",
        company="Tokyo Tech Co.",
        location="Tokyo",
        url="https://example.com/jobs/123",
        description_snippet="Build APIs with Python and FastAPI.",
    )

    # 2) DB table model instance (has DB-only fields like url_hash)
    db_row = JobListing(
        title="Backend Engineer",
        company="Tokyo Tech Co.",
        location="Tokyo",
        url="https://example.com/jobs/123",
        description_snippet="Build APIs with Python and FastAPI.",
        url_hash="abc123hash",
    )

    # 3) API response schema instance (shape tailored to API output)
    api_response = JobListingResponse(
        id=1,
        title="Backend Engineer",
        company="Tokyo Tech Co.",
        location="Tokyo",
        url="https://example.com/jobs/123",
        description_snippet="Build APIs with Python and FastAPI.",
        scraped_at=datetime.utcnow(),
    )

    print("\n=== Relationship to Pydantic ===")
    print(f"JobListingBase is a Pydantic model: {hasattr(JobListingBase, 'model_dump')}")

    print("\n=== table=True vs no table=True ===")
    print(f"JobListing has SQLAlchemy table metadata: {hasattr(JobListing, '__table__')}")
    print(
        "JobListingResponse has SQLAlchemy table metadata: "
        f"{hasattr(JobListingResponse, '__table__')}"
    )
    print(f"JobListing table name: {JobListing.__tablename__}")

    print("\n=== Class inheritance in practice ===")
    print("Shared fields come from JobListingBase:")
    print(f"- base.title: {base.title}")
    print(f"- db_row.title: {db_row.title}")
    print(f"- api_response.title: {api_response.title}")

    print("\n=== Data examples ===")
    print("Base schema:", base.model_dump())
    print("DB model:", db_row.model_dump())
    print("API response schema:", api_response.model_dump())


if __name__ == "__main__":
    main()
