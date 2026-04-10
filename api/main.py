"""Application entrypoint for FastAPI."""

from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from scheduler.tasks import run_daily_scrape

# Load .env values into environment variables at startup
load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Start APScheduler on app startup and shut it down on app exit."""
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Tokyo"))
    scheduler.add_job(run_daily_scrape, "cron", hour=7, minute=0, id="daily_scrape")
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title="Python Job Scraper API", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health endpoint for service monitoring."""
    return {"status": "ok"}
