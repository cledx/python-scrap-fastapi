"""Command line interface for scraper utilities."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict

from scraper.daijob import DAIJOB_JOBS_URL, scrape_daijob_jobs
from scraper.gaijinpot import GAIJINPOT_JOBS_URL, scrape_gaijinpot_jobs
from scraper.tokyodev import TOKYODEV_JOBS_URL, scrape_tokyodev
from scraper.wantedly import WANTEDLY_TOKYO_PROJECTS_URL, scrape_wantedly


async def _run_gaijinpot(url: str, timeout: float) -> int:
    listings = await scrape_gaijinpot_jobs(url=url, timeout_seconds=timeout)
    print(json.dumps([asdict(job) for job in listings], indent=2, ensure_ascii=False))
    return 0


async def _run_daijob(url: str, timeout: float) -> int:
    listings = await scrape_daijob_jobs(url=url, timeout_seconds=timeout)
    print(json.dumps([asdict(job) for job in listings], indent=2, ensure_ascii=False))
    return 0


async def _run_tokyodev(url: str, timeout: float) -> int:
    listings = await scrape_tokyodev(url=url, timeout_seconds=timeout)
    print(json.dumps(listings, indent=2, ensure_ascii=False))
    return 0


async def _run_wantedly(url: str, timeout: float) -> int:
    listings = await scrape_wantedly(url=url, timeout_seconds=timeout)
    print(json.dumps(listings, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Python Scrap FastAPI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gaijinpot_parser = subparsers.add_parser(
        "gaijinpot", help="Scrape GaijinPot and print JSON results"
    )
    gaijinpot_parser.add_argument("--url", default=None, help="Override GaijinPot source URL")
    gaijinpot_parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds",
    )
    daijob_parser = subparsers.add_parser("daijob", help="Scrape Daijob and print JSON results")
    daijob_parser.add_argument("--url", default=None, help="Override Daijob source URL")
    daijob_parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds",
    )
    tokyodev_parser = subparsers.add_parser("tokyodev", help="Scrape TokyoDev and print JSON results")
    tokyodev_parser.add_argument("--url", default=None, help="Override TokyoDev source URL")
    tokyodev_parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds",
    )
    wantedly_parser = subparsers.add_parser("wantedly", help="Scrape Wantedly and print JSON results")
    wantedly_parser.add_argument("--url", default=None, help="Override Wantedly projects listing URL")
    wantedly_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds",
    )

    args = parser.parse_args()

    if args.command == "gaijinpot":
        url = args.url or GAIJINPOT_JOBS_URL
        return asyncio.run(_run_gaijinpot(url=url, timeout=args.timeout))
    if args.command == "daijob":
        url = args.url or DAIJOB_JOBS_URL
        return asyncio.run(_run_daijob(url=url, timeout=args.timeout))
    if args.command == "tokyodev":
        url = args.url or TOKYODEV_JOBS_URL
        return asyncio.run(_run_tokyodev(url=url, timeout=args.timeout))
    if args.command == "wantedly":
        url = args.url or WANTEDLY_TOKYO_PROJECTS_URL
        return asyncio.run(_run_wantedly(url=url, timeout=args.timeout))

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
