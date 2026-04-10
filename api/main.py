"""Application entrypoint for FastAPI."""

from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from api.jobs import router as jobs_router

# Load .env values into environment variables at startup
load_dotenv()

app = FastAPI(title="Python Job Scraper API")
app.include_router(jobs_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health endpoint for service monitoring."""
    return {"status": "ok"}
