"""Scraper logic package."""

from .gaijinpot import GaijinpotJobListing, parse_gaijinpot_jobs, scrape_gaijinpot_jobs

__all__ = ["GaijinpotJobListing", "parse_gaijinpot_jobs", "scrape_gaijinpot_jobs"]
