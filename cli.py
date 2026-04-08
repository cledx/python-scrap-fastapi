"""Command line interface for scraper utilities."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict

from scraper.daijob import DAIJOB_JOBS_URL, scrape_daijob_jobs
from scraper.gaijinpot import GAIJINPOT_JOBS_URL, scrape_gaijinpot_jobs


async def _run_gaijinpot(url: str, timeout: float) -> int:
    listings = await scrape_gaijinpot_jobs(url=url, timeout_seconds=timeout)
    print(json.dumps([asdict(job) for job in listings], indent=2, ensure_ascii=False))
    return 0


async def _run_daijob(url: str, timeout: float) -> int:
    listings = await scrape_daijob_jobs(url=url, timeout_seconds=timeout)
    print(json.dumps([asdict(job) for job in listings], indent=2, ensure_ascii=False))
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

    args = parser.parse_args()

    if args.command == "gaijinpot":
        url = args.url or GAIJINPOT_JOBS_URL
        return asyncio.run(_run_gaijinpot(url=url, timeout=args.timeout))
    if args.command == "daijob":
        url = args.url or DAIJOB_JOBS_URL
        return asyncio.run(_run_daijob(url=url, timeout=args.timeout))

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
