"""Scraper logic package."""

from .daijob import DaijobJobListing, parse_daijob_jobs, scrape_daijob_jobs
from .gaijinpot import GaijinpotJobListing, parse_gaijinpot_jobs, scrape_gaijinpot_jobs
from .tokyodev import TOKYODEV_JOBS_URL, parse_tokyodev_jobs, scrape_tokyodev
from .wantedly import WANTEDLY_TOKYO_PROJECTS_URL, parse_wantedly_projects_html, scrape_wantedly

__all__ = [
    "DaijobJobListing",
    "parse_daijob_jobs",
    "scrape_daijob_jobs",
    "GaijinpotJobListing",
    "parse_gaijinpot_jobs",
    "scrape_gaijinpot_jobs",
    "TOKYODEV_JOBS_URL",
    "parse_tokyodev_jobs",
    "scrape_tokyodev",
    "WANTEDLY_TOKYO_PROJECTS_URL",
    "parse_wantedly_projects_html",
    "scrape_wantedly",
]
