import re
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings

_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _extract_title(html: str) -> str:
    match = _TITLE_PATTERN.search(html)
    if not match:
        return ""

    return re.sub(r"\s+", " ", match.group(1)).strip()


def _build_crawlbase_url(target_url: str) -> str:
    settings = get_settings()
    if not settings.crawlbase_token:
        raise RuntimeError("CRAWLBASE_TOKEN is not configured")

    query = urlencode(
        {
            "token": settings.crawlbase_token,
            "url": target_url,
            "javascript": "true",
            "page_wait": "5000",
            "country": "US",
        }
    )
    return f"{settings.crawlbase_api_url.rstrip('/')}/?{query}"


async def scrape_url(
    url: str,
    *,
    wait_until: str = "networkidle",
    selector: str | None = None,
) -> dict[str, Any]:
    del wait_until, selector  # Crawlbase handles rendering server-side.

    settings = get_settings()
    api_url = _build_crawlbase_url(url)

    async with httpx.AsyncClient(
        timeout=settings.crawlbase_timeout_s,
        follow_redirects=True,
    ) as client:
        response = await client.get(api_url)

    html = response.text
    pc_status = int(response.headers.get("pc_status", response.status_code))
    original_status = int(response.headers.get("original_status", pc_status))
    final_url = response.headers.get("url", url)

    if pc_status != 200:
        raise RuntimeError(
            f"Crawlbase request failed with pc_status={pc_status}: {html[:500]}"
        )

    return {
        "url": final_url,
        "status": original_status,
        "title": _extract_title(html),
        "html": html,
    }
