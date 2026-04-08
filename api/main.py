"""Application entrypoint for FastAPI."""

from dotenv import load_dotenv
from fastapi import FastAPI

# Load .env values into environment variables at startup
load_dotenv()

app = FastAPI(title="Python Job Scraper API")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health endpoint for service monitoring."""
    return {"status": "ok"}
