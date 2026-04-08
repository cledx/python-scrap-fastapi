"""GaijinPot job scraper using httpx + BeautifulSoup."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

GAIJINPOT_JOBS_URL = "https://jobs.gaijinpot.com/en/job?keywords=&function%5B%5D=1000&function%5B%5D=7000&region=JP-13&english_ability=&language=&other_language=&career_level=&employment_terms=&employer_type=&remote_work_ok=0&overseas_application=0&has_video_presentation=0"


@dataclass(slots=True)
class GaijinpotJobListing:
    """Structured listing fields required by the project."""

    title: str
    company: str
    location: str
    url: str
    date_posted: str
    description_snippet: str


def _text_or_empty(node: Tag | None) -> str:
    """Normalize node text while tolerating missing nodes."""
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


def _dl_dd_after_dt(card: Tag, label: str) -> str:
    """Return text from <dd> following <dt> whose text matches label (GaijinPot list cards)."""
    label_norm = label.strip().lower()
    for dt in card.select("dl.dl-inline-sm dt"):
        if _text_or_empty(dt).strip().rstrip(":").lower() != label_norm:
            continue
        nxt = dt.find_next_sibling()
        if nxt and nxt.name == "dd":
            return _text_or_empty(nxt)
    return ""


def _fix_href_query_ampersands(href: str) -> str:
    """Repair hrefs where unescaped &param= was parsed as an HTML entity (e.g. &region -> ®ion)."""
    return href.replace("®ion=", "&region=")


def _job_detail_href(tag: Tag) -> str | None:
    if not tag.has_attr("href"):
        return None
    href = tag["href"]
    if not isinstance(href, str):
        return None
    h = href.strip()
    if "/en/job/" not in h:
        return None
    path = h.split("?", 1)[0]
    slug = path.rsplit("/", 1)[-1]
    if slug.isdigit():
        return h
    return None


def _parse_job_card(card: Tag, base_url: str) -> GaijinpotJobListing | None:
    # Standalone <a> rows (fallback list): title/href live on the element itself.
    if card.name == "a":
        raw_url = _job_detail_href(card)
        if raw_url is None:
            return None
        title = _text_or_empty(card)
        if not title:
            return None
        raw_url = _fix_href_query_ampersands(raw_url)
        return GaijinpotJobListing(
            title=title,
            company="",
            location="",
            url=urljoin(base_url, raw_url),
            date_posted="",
            description_snippet="",
        )

    title = _pick_first_text(
        card,
        [
            "h3.card-heading a",
            "h2 a",
            "h3 a",
            "a[data-testid*='job']",
            "a[href*='/en/job/']",
            "a[href*='/job/']",
            "a[href*='/jobs/']",
        ],
    )
    raw_url = _pick_first_href(
        card,
        ["h3.card-heading a", "h2 a", "h3 a", "a[href*='/en/job/']", "a[href]"],
    )
    if not raw_url and card.has_attr("data-href"):
        dh = card.get("data-href")
        if isinstance(dh, str) and "/en/job/" in dh:
            raw_url = dh.strip()

    company = _dl_dd_after_dt(card, "Company") or _pick_first_text(
        card,
        [
            ".company",
            ".company-name",
            "[data-testid*='company']",
            "span[itemprop='name']",
        ],
    )
    location = _dl_dd_after_dt(card, "Location") or _pick_first_text(
        card,
        [
            ".location",
            ".job-location",
            "[data-testid*='location']",
            "li.location",
        ],
    )
    date_posted = _dl_dd_after_dt(card, "Date") or _pick_first_text(
        card,
        [
            "time",
            ".posted-date",
            ".date-posted",
            "[data-testid*='posted']",
        ],
    )
    description_snippet = _dl_dd_after_dt(card, "Requirements") or _pick_first_text(
        card,
        [
            ".description",
            ".job-description",
            ".summary",
            "p",
        ],
    )

    if not title or not raw_url:
        return None

    raw_url = _fix_href_query_ampersands(raw_url)
    return GaijinpotJobListing(
        title=title,
        company=company,
        location=location,
        url=urljoin(base_url, raw_url),
        date_posted=date_posted,
        description_snippet=description_snippet,
    )


def parse_gaijinpot_jobs(html: str, *, base_url: str = GAIJINPOT_JOBS_URL) -> list[GaijinpotJobListing]:
    """Parse GaijinPot jobs HTML into structured listings."""
    soup = BeautifulSoup(html, "html.parser")

    # Current GaijinPot search results: one card per job (clickable row).
    cards = soup.select("div.card.gpjs-open-link[data-href*='/en/job/']")
    if not cards:
        cards = soup.select("div.card.gpjs-open-link")
    if not cards:
        cards = soup.select(
            "article, li.job, .job, .job-card, [data-testid*='job-card'], [class*='job-listing']"
        )
    if not cards:
        cards = soup.select("a[href*='/en/job/']")
    if not cards:
        cards = soup.select("a[href*='/jobs/'], a[href*='/job/']")

    listings: list[GaijinpotJobListing] = []
    seen_urls: set[str] = set()

    for card in cards:
        parsed = _parse_job_card(card, base_url)
        if parsed is None:
            continue
        if parsed.url in seen_urls:
            continue
        seen_urls.add(parsed.url)
        listings.append(parsed)

    return listings


async def scrape_gaijinpot_jobs(
    *,
    url: str = GAIJINPOT_JOBS_URL,
    timeout_seconds: float = 20.0,
) -> list[GaijinpotJobListing]:
    """Fetch and scrape GaijinPot jobs."""
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    return parse_gaijinpot_jobs(response.text, base_url=url)
