"""Scraper logic package."""

from .daijob import DaijobJobListing, parse_daijob_jobs, scrape_daijob_jobs
from .gaijinpot import GaijinpotJobListing, parse_gaijinpot_jobs, scrape_gaijinpot_jobs

__all__ = [
    "DaijobJobListing",
    "parse_daijob_jobs",
    "scrape_daijob_jobs",
    "GaijinpotJobListing",
    "parse_gaijinpot_jobs",
    "scrape_gaijinpot_jobs",
]
