from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from api.main import app
from models.database import get_session
from models.job_listing import JobListing


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


@pytest.fixture()
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_jobs(session: Session) -> list[JobListing]:
    now = datetime.utcnow()
    jobs = [
        JobListing(
            title="Backend Engineer",
            company="Acme",
            location="Tokyo",
            url="https://example.com/jobs/1",
            url_hash="hash-1",
            description_snippet="Build APIs",
            summary="Great backend role",
            pros=json.dumps(["Remote", "Mentorship"]),
            cons=json.dumps(["On-call"]),
            seen=False,
            scraped_at=now,
        ),
        JobListing(
            title="Data Engineer",
            company="Beta",
            location="Tokyo",
            url="https://example.com/jobs/2",
            url_hash="hash-2",
            description_snippet="Pipelines and ETL",
            summary="Strong data role",
            pros=json.dumps(["Modern stack"]),
            cons=json.dumps(["Legacy migration"]),
            seen=True,
            scraped_at=now,
        ),
    ]
    for job in jobs:
        session.add(job)
    session.commit()
    for job in jobs:
        session.refresh(job)
    return jobs


def test_get_jobs_returns_200_and_list(client: TestClient, seeded_jobs: list[JobListing]) -> None:
    response = client.get("/jobs")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == len(seeded_jobs)
    assert all("id" in item for item in payload)


def test_get_jobs_seen_false_filters_correctly(
    client: TestClient,
    seeded_jobs: list[JobListing],
) -> None:
    response = client.get("/jobs?seen=false")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["id"] == seeded_jobs[0].id
    assert payload[0]["seen"] is False


def test_get_job_by_id_returns_200_with_correct_shape(
    client: TestClient,
    seeded_jobs: list[JobListing],
) -> None:
    job_id = seeded_jobs[0].id
    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "title",
        "company",
        "location",
        "url",
        "summary",
        "pros",
        "cons",
        "description_snippet",
    }
    assert payload["title"] == seeded_jobs[0].title
    assert payload["pros"] == ["Remote", "Mentorship"]
    assert payload["cons"] == ["On-call"]


def test_get_job_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/jobs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_patch_job_seen_returns_updated_object(
    client: TestClient,
    seeded_jobs: list[JobListing],
) -> None:
    job_id = seeded_jobs[0].id
    response = client.patch(f"/jobs/{job_id}/seen")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == job_id
    assert payload["seen"] is True
