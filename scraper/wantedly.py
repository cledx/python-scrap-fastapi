"""Wantedly job scraper via Next.js embedded Apollo state (httpx + JSON)."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

# Tokyo filter: area is applied server-side in the listing query.
WANTEDLY_TOKYO_PROJECTS_URL = "https://www.wantedly.com/projects?area=tokyo"

WANTEDLY_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(?P<json>.*?)</script>',
    re.DOTALL,
)


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": WANTEDLY_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }


def _extract_next_data_json(html: str) -> dict[str, Any] | None:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        return json.loads(match.group("json"))
    except json.JSONDecodeError:
        return None


def _resolve_ref(cache: dict[str, Any], ref: Any) -> dict[str, Any] | None:
    if not isinstance(ref, dict):
        return None
    key = ref.get("__ref")
    if not isinstance(key, str):
        return None
    node = cache.get(key)
    return node if isinstance(node, dict) else None


def _find_searched_job_post_edges(gateway: dict[str, Any]) -> list[dict[str, Any]]:
    root = gateway.get("ROOT_QUERY")
    if not isinstance(root, dict):
        return []
    index = root.get("projectIndexPageJobPostIndex")
    if not isinstance(index, dict):
        return []
    for key, value in index.items():
        if not key.startswith("searchedJobPosts("):
            continue
        if not isinstance(value, dict):
            continue
        edges = value.get("edges")
        if isinstance(edges, list):
            return edges
    return []


def _snippet_from_job(job: dict[str, Any]) -> str:
    desc = job.get("detailDescription")
    if not isinstance(desc, dict):
        return ""
    body = desc.get("plainBody")
    if not isinstance(body, str):
        return ""
    text = " ".join(body.split())
    return text[:280].strip()


def _listing_from_job(
    gateway: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, str] | None:
    job_id = str(job.get("id") or "").strip()
    title = str(job.get("title") or "").strip()
    if not job_id or not title:
        return None

    company_name = ""
    company_ref = job.get("company")
    company = _resolve_ref(gateway, company_ref)
    if company is not None:
        company_name = str(company.get("name") or "").strip()

    # Listing uses `area=tokyo`; no per-row address in this payload.
    location = "Tokyo"

    return {
        "title": title,
        "company": company_name,
        "location": location,
        "url": f"https://www.wantedly.com/projects/{job_id}",
        "description_snippet": _snippet_from_job(job),
    }


def parse_wantedly_projects_html(html: str) -> list[dict[str, str]]:
    """Parse Wantedly projects HTML (SSR __NEXT_DATA__ / Apollo cache) into listing dicts."""
    data = _extract_next_data_json(html)
    if not data:
        return []

    page_props = data.get("props")
    page_props = page_props if isinstance(page_props, dict) else {}
    inner = page_props.get("pageProps")
    inner = inner if isinstance(inner, dict) else {}
    apollo = inner.get("__apollo")
    apollo = apollo if isinstance(apollo, dict) else {}
    gateway = apollo.get("graphqlGatewayInitialState")
    if not isinstance(gateway, dict):
        return []

    listings: list[dict[str, str]] = []
    seen: set[str] = set()

    for edge in _find_searched_job_post_edges(gateway):
        if not isinstance(edge, dict):
            continue
        node = edge.get("node")
        if not isinstance(node, dict):
            continue
        job = _resolve_ref(gateway, node.get("jobPost"))
        if job is None:
            continue
        listing = _listing_from_job(gateway, job)
        if listing is None:
            continue
        key = listing["url"]
        if key in seen:
            continue
        seen.add(key)
        listings.append(listing)

    return listings


async def scrape_wantedly(
    *,
    url: str = WANTEDLY_TOKYO_PROJECTS_URL,
    timeout_seconds: float = 30.0,
) -> list[dict]:
    """Fetch Tokyo-area Wantedly project listings from the SSR page JSON."""
    headers = _default_headers()
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        listings = parse_wantedly_projects_html(response.text)
        if listings:
            return listings

    raise RuntimeError("Wantedly response did not contain parseable job listings.")
