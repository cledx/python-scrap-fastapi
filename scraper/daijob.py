"""Daijob job scraper using httpx + BeautifulSoup."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

DAIJOB_JOBS_URL = (
    "https://www.daijob.com/en/jobs/search_result?job_types[]=401&job_types[]=402&job_types[]=403&job_types[]=404&job_types[]=405&job_types[]=301&job_types[]=302&job_types[]=304&job_types[]=305&job_types[]=307&job_types[]=309&job_types[]=310&job_types[]=311&job_types[]=315&job_types[]=400&jt[]=301&jt[]=302&jt[]=304&jt[]=305&jt[]=307&jt[]=309&jt[]=310&jt[]=311&jt[]=315&jt[]=400&working_a_locations[]=230&working_a_locations[]=102&working_a_locations[]=118&working_b_locations[]=230&working_b_locations[]=102&working_b_locations[]=115&job_search_form_hidden=1&career_levels[]=40&career_levels[]=50"
)


@dataclass(slots=True)
class DaijobJobListing:
    """Structured listing fields required by the project."""

    title: str
    company: str
    location: str
    url: str
    date_posted: str
    description_snippet: str


def _text_or_empty(node: Tag | None) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _pick_first_text(card: Tag, selectors: list[str]) -> str:
    for selector in selectors:
        value = _text_or_empty(card.select_one(selector))
        if value:
            return value
    return ""


def _pick_first_href(card: Tag, selectors: list[str]) -> str:
    for selector in selectors:
        anchor = card.select_one(selector)
        if anchor and anchor.has_attr("href"):
            href = anchor["href"]
            if isinstance(href, str) and href.strip():
                return href.strip()
    return ""


def _normalize_daijob_href(href: str) -> str:
    # Daijob detail pages are usually /en/jobs/detail/<id>.
    if href.startswith("/"):
        return href
    detail_match = re.search(r"(/en/jobs/detail/\d+)", href)
    if detail_match:
        return detail_match.group(1)
    return href


def _extract_company(card: Tag) -> str:
    company = _pick_first_text(
        card,
        [
            "[class*='company']",
            ".company_name",
            ".company",
            "a[href*='/company/']",
        ],
    )
    if company:
        return company

    # Fallback for simple text dumps where company line often appears before title.
    text_lines = [ln.strip() for ln in card.get_text("\n", strip=True).splitlines() if ln.strip()]
    for line in text_lines:
        if line in {"HOT", "NEW", "Employer", "Recruiter", "Staffing Agency"}:
            continue
        if line.startswith("## "):
            break
        if len(line) > 1:
            return line
    return ""


def _extract_location(card: Tag) -> str:
    location = _pick_first_text(
        card,
        [
            "[class*='location']",
            ".work_location",
            "li.location",
        ],
    )
    if location:
        return location

    text = card.get_text("\n", strip=True)
    location_match = re.search(r"Location\s+(.*?)\s+(?:Salary|Japanese Level|Job Description)", text, re.S)
    if not location_match:
        return ""
    return " ".join(location_match.group(1).split())


def _extract_description_snippet(card: Tag) -> str:
    snippet = _pick_first_text(
        card,
        [
            "[class*='description']",
            ".job_description",
            ".description",
            "p",
        ],
    )
    if snippet:
        return snippet

    text = card.get_text("\n", strip=True)
    snippet_match = re.search(r"Job Description\s+(.*?)\s+(?:Like|View Full Listing|$)", text, re.S)
    if not snippet_match:
        return ""
    return " ".join(snippet_match.group(1).split())


def _extract_date_posted(card: Tag) -> str:
    return _pick_first_text(
        card,
        [
            "time",
            "[class*='date']",
            "[class*='updated']",
            "[class*='activated']",
        ],
    )


def _parse_job_card(card: Tag, base_url: str) -> DaijobJobListing | None:
    title = _pick_first_text(
        card,
        [
            "h3 a",
            "h2 a",
            "h3",
            "h2",
            "a[href*='/en/jobs/detail/']",
        ],
    )
    raw_url = _pick_first_href(
        card,
        [
            "h3 a",
            "h2 a",
            "a[href*='/en/jobs/detail/']",
            "a[href]",
        ],
    )

    if raw_url:
        raw_url = _normalize_daijob_href(raw_url)

    if not title:
        # Markdown/text fallback: "## <title>".
        text = card.get_text("\n", strip=True)
        title_match = re.search(r"##\s+(.+)", text)
        if title_match:
            title = " ".join(title_match.group(1).split())

    if not raw_url:
        # Best-effort fallback if hrefs are stripped from exported content.
        detail_match = re.search(r"/en/jobs/detail/\d+", card.get_text(" ", strip=True))
        if detail_match:
            raw_url = detail_match.group(0)

    if not title or not raw_url:
        return None

    return DaijobJobListing(
        title=title,
        company=_extract_company(card),
        location=_extract_location(card),
        url=urljoin(base_url, raw_url),
        date_posted=_extract_date_posted(card),
        description_snippet=_extract_description_snippet(card),
    )


def _parse_text_dump_fallback(source: str, *, base_url: str) -> list[DaijobJobListing]:
    # Handles text/markdown exports where each listing starts with "## <title>".
    listings: list[DaijobJobListing] = []
    blocks = re.split(r"\n(?=##\s+)", source)
    seen_urls: set[str] = set()

    for block in blocks:
        title_match = re.search(r"##\s+(.+)", block)
        if not title_match:
            continue
        title = " ".join(title_match.group(1).split())

        company = ""
        company_match = re.search(r"\n([^\n]+)\n\n##\s+", block)
        if company_match:
            candidate = company_match.group(1).strip()
            if not candidate.startswith("("):
                company = candidate

        location = ""
        location_match = re.search(r"Location\s+(.*?)\s+Salary", block, re.S)
        if location_match:
            location = " ".join(location_match.group(1).split())

        snippet = ""
        snippet_match = re.search(r"Job Description\s+(.*?)\s+(?:Like|View Full Listing|$)", block, re.S)
        if snippet_match:
            snippet = " ".join(snippet_match.group(1).split())

        detail_match = re.search(r"/en/jobs/detail/\d+", block)
        if not detail_match:
            continue
        url = urljoin(base_url, detail_match.group(0))
        if url in seen_urls:
            continue
        seen_urls.add(url)
        listings.append(
            DaijobJobListing(
                title=title,
                company=company,
                location=location,
                url=url,
                date_posted="",
                description_snippet=snippet,
            )
        )
    return listings


def parse_daijob_jobs(html: str, *, base_url: str = DAIJOB_JOBS_URL) -> list[DaijobJobListing]:
    """Parse Daijob jobs HTML into structured listings."""
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(
        "article, li, div[class*='job'], div[class*='search-result'], [data-job-id], [data-id]"
    )
    listings: list[DaijobJobListing] = []
    seen_urls: set[str] = set()

    for card in cards:
        parsed = _parse_job_card(card, base_url)
        if parsed is None:
            continue
        if parsed.url in seen_urls:
            continue
        seen_urls.add(parsed.url)
        listings.append(parsed)

    if listings:
        return listings

    # If page is heavily script-rendered or converted to plain text, try text fallback.
    return _parse_text_dump_fallback(html, base_url=base_url)


async def scrape_daijob_jobs(
    *,
    url: str = DAIJOB_JOBS_URL,
    timeout_seconds: float = 20.0,
) -> list[DaijobJobListing]:
    """Fetch and scrape Daijob jobs."""
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    return parse_daijob_jobs(response.text, base_url=url)
