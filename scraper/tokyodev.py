"""TokyoDev job scraper using httpx + BeautifulSoup."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

TOKYODEV_JOBS_URL = "https://www.tokyodev.com/jobs"
TOKYODEV_JINA_MIRROR_URL = "https://r.jina.ai/http://www.tokyodev.com/jobs"
TOKYODEV_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)


def _text_or_empty(node: Tag | None) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(" ", strip=True).split())


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _looks_like_cloudflare_challenge(html: str) -> bool:
    source = html.lower()
    return (
        "just a moment..." in source
        or "cdn-cgi/challenge-platform" in source
        or "enable javascript and cookies to continue" in source
    )


def _default_headers() -> dict[str, str]:
    # More browser-like defaults reduce odds of simple bot heuristics triggering.
    return {
        "User-Agent": TOKYODEV_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


def _extract_company(anchor: Tag) -> str:
    container = anchor.find_parent(["li", "article", "section", "div"])
    if container is None:
        return ""

    # Company links are typically "/companies/<slug>" whereas jobs include "/jobs/".
    for company_anchor in container.select("a[href*='/companies/']"):
        href = company_anchor.get("href")
        if not isinstance(href, str):
            continue
        if "/jobs/" in href:
            continue
        text = _text_or_empty(company_anchor)
        if text:
            return text
    return ""


def _extract_location(context_text: str) -> str:
    lowered = context_text.lower()
    if "fully remote" in lowered:
        return "Fully remote"
    if "partially remote" in lowered:
        return "Partially remote"
    if "on-site" in lowered or "onsite" in lowered:
        return "On-site"
    if "japan residents only" in lowered:
        return "Japan residents only"
    if "apply from abroad" in lowered:
        return "Apply from abroad"
    return ""


def _extract_description_snippet(anchor: Tag, title: str, company: str) -> str:
    container = anchor.find_parent(["li", "article", "section", "div"])
    if container is None:
        return ""

    text = _text_or_empty(container)
    if not text:
        return ""
    snippet = text
    if title:
        snippet = snippet.replace(title, "").strip()
    if company:
        snippet = snippet.replace(company, "").strip()
    return snippet[:280].strip()


def _parse_from_dom(html: str, *, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for anchor in soup.select("a[href*='/companies/'][href*='/jobs/']"):
        href = anchor.get("href")
        if not isinstance(href, str) or not href.strip():
            continue

        title = _text_or_empty(anchor)
        if not title:
            continue

        url = urljoin(base_url, href.strip())
        if url in seen_urls:
            continue

        company = _extract_company(anchor)
        container = anchor.find_parent(["li", "article", "section", "div"])
        context_text = _text_or_empty(container) if container else ""
        location = _extract_location(context_text)
        description_snippet = _extract_description_snippet(anchor, title=title, company=company)

        seen_urls.add(url)
        listings.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description_snippet": description_snippet,
            }
        )
    return listings


def _parse_text_dump_fallback(source: str, *, base_url: str) -> list[dict[str, str]]:
    # Handles markdown/text dumps where each listing is in:
    # "#### [Job Title](.../companies/.../jobs/...)"
    job_pattern = re.compile(
        r"####\s+\[(?P<title>.+?)\]\((?P<url>https?://[^\s)]+/companies/[^\s)]+/jobs/[^\s)]+)\)",
        re.M,
    )
    company_pattern = re.compile(r"###\s+\[(?P<company>.+?)\]\((?P<url>https?://[^\s)]+/companies/[^\s)]+)\)")

    listings: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    company_matches = list(company_pattern.finditer(source))
    job_matches = list(job_pattern.finditer(source))
    if not job_matches:
        return listings

    company_idx = 0
    current_company = ""
    for job_match in job_matches:
        while company_idx < len(company_matches) and company_matches[company_idx].start() < job_match.start():
            current_company = _clean_text(company_matches[company_idx].group("company"))
            company_idx += 1

        title = _clean_text(job_match.group("title"))
        url = urljoin(base_url, job_match.group("url"))
        if not title or url in seen_urls:
            continue

        # Capture a short context window after the heading and infer location-like signals.
        tail = source[job_match.end() : job_match.end() + 400]
        snippet = _clean_text(tail).strip()
        location = _extract_location(snippet)

        listings.append(
            {
                "title": title,
                "company": current_company,
                "location": location,
                "url": url,
                "description_snippet": snippet[:280],
            }
        )
        seen_urls.add(url)

    return listings


def parse_tokyodev_jobs(html: str, *, base_url: str = TOKYODEV_JOBS_URL) -> list[dict[str, str]]:
    """Parse TokyoDev jobs HTML into listing dictionaries."""
    listings = _parse_from_dom(html, base_url=base_url)
    if listings:
        return listings
    return _parse_text_dump_fallback(html, base_url=base_url)


async def scrape_tokyodev(
    *,
    url: str = TOKYODEV_JOBS_URL,
    timeout_seconds: float = 20.0,
) -> list[dict[str, str]]:
    """Fetch and scrape TokyoDev jobs."""
    headers = _default_headers()
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        if response.status_code < 400 and not _looks_like_cloudflare_challenge(response.text):
            return parse_tokyodev_jobs(response.text, base_url=url)

        # Fallback endpoint that can return a static text/markdown rendering.
        # This keeps the scraper operational when the direct path is challenged.
        mirror_response = await client.get(TOKYODEV_JINA_MIRROR_URL, headers=headers)
        mirror_response.raise_for_status()
        listings = parse_tokyodev_jobs(mirror_response.text, base_url=url)
        if listings:
            return listings

    if response.status_code == 403 or _looks_like_cloudflare_challenge(response.text):
        raise RuntimeError(
            "TokyoDev returned 403/Cloudflare challenge and mirror fallback produced no listings."
        )
    response.raise_for_status()
    raise RuntimeError("TokyoDev response did not contain parseable job listings.")
