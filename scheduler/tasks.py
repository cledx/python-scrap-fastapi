"""Scraping task entry points for scheduled jobs."""

from scraper.daijob import scrape_daijob_jobs
from scraper.gaijinpot import scrape_gaijinpot_jobs
from scraper.tokyodev import scrape_tokyodev
from scraper.wantedly import scrape_wantedly

__all__ = [
    "scrape_daijob_jobs",
    "scrape_gaijinpot_jobs",
    "scrape_tokyodev",
    "scrape_wantedly",
]
