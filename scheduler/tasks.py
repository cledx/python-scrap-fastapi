"""Scraping task entry points for scheduled jobs."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any

from sqlmodel import Session, select

from models.database import engine
from models.job_listing import JobListing
from scraper.ai_service import enrich_listing
from scraper.daijob import scrape_daijob_jobs
from scraper.gaijinpot import scrape_gaijinpot_jobs
from scraper.tokyodev import scrape_tokyodev
from scraper.wantedly import scrape_wantedly

logger = logging.getLogger(__name__)


def _normalize_listing(raw_listing: Any) -> dict[str, str]:
    if is_dataclass(raw_listing):
        listing = asdict(raw_listing)
    elif isinstance(raw_listing, dict):
        listing = raw_listing
    else:
        raise TypeError(f"Unsupported listing type: {type(raw_listing)!r}")

    return {
        "title": str(listing.get("title", "")).strip(),
        "company": str(listing.get("company", "")).strip(),
        "location": str(listing.get("location", "")).strip(),
        "url": str(listing.get("url", "")).strip(),
        "description_snippet": str(listing.get("description_snippet", "")).strip(),
        "date_posted": str(listing.get("date_posted", "")).strip(),
    }


def _upsert_listing(
    session: Session,
    *,
    listing: dict[str, str],
    enrichment: dict[str, Any],
) -> None:
    url_hash = sha256(listing["url"].encode("utf-8")).hexdigest()
    db_listing = session.exec(select(JobListing).where(JobListing.url_hash == url_hash)).first()

    if db_listing is None:
        db_listing = JobListing(
            title=listing["title"],
            company=listing["company"],
            location=listing["location"],
            url=listing["url"],
            url_hash=url_hash,
            description_snippet=listing["description_snippet"],
            posted_at=None,
            seen=False,
        )
        session.add(db_listing)

    db_listing.title = listing["title"]
    db_listing.company = listing["company"]
    db_listing.location = listing["location"]
    db_listing.url = listing["url"]
    db_listing.description_snippet = listing["description_snippet"]
    db_listing.summary = str(enrichment.get("summary", "")).strip() or None
    db_listing.pros = json.dumps(enrichment.get("pros", []), ensure_ascii=False)
    db_listing.cons = json.dumps(enrichment.get("cons", []), ensure_ascii=False)
    db_listing.scraped_at = datetime.utcnow()

    session.commit()


async def scrape_enrich_and_persist_listings() -> dict[str, int]:
    """Run scrape + enrichment pipeline and persist rows to PostgreSQL."""
    source_jobs = [
        ("gaijinpot", scrape_gaijinpot_jobs),
        ("daijob", scrape_daijob_jobs),
        ("tokyodev", scrape_tokyodev),
        ("wantedly", scrape_wantedly),
    ]

    stats = {"processed": 0, "saved": 0, "failed": 0}

    with Session(engine) as session:
        for source_name, scrape_fn in source_jobs:
            try:
                listings = await scrape_fn()
            except Exception:
                logger.exception("Source scrape failed; continuing run", extra={"source": source_name})
                continue

            for raw_listing in listings:
                stats["processed"] += 1
                try:
                    listing = _normalize_listing(raw_listing)
                    if not listing["url"]:
                        raise ValueError("Listing url is required for persistence")
                    enrichment = await enrich_listing(listing["description_snippet"])
                    _upsert_listing(session, listing=listing, enrichment=enrichment)
                    stats["saved"] += 1
                except Exception:
                    session.rollback()
                    stats["failed"] += 1
                    logger.exception(
                        "Listing enrichment/persistence failed; continuing run",
                        extra={"source": source_name},
                    )

    logger.info("Scheduler scrape run completed", extra=stats)
    return stats


__all__ = [
    "scrape_daijob_jobs",
    "scrape_gaijinpot_jobs",
    "scrape_tokyodev",
    "scrape_wantedly",
    "scrape_enrich_and_persist_listings",
]
