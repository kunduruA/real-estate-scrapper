import asyncio
import random
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, async_playwright

from app.config import get_settings

STEALTH_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
STEALTH_VIEWPORT = {"width": 1920, "height": 1080}
STEALTH_HEADERS = {"Accept-Language": "en-US,en;q=0.9"}

_playwright = None
_browser: Browser | None = None
_browser_lock = asyncio.Lock()


async def _get_browser() -> Browser:
    global _playwright, _browser

    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            _playwright = await async_playwright().start()
            settings = get_settings()
            _browser = await _playwright.chromium.launch(
                headless=settings.playwright_headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process",
                ],
            )

    return _browser


@asynccontextmanager
async def _page_context():
    browser = await _get_browser()
    settings = get_settings()
    context = await browser.new_context(
        user_agent=STEALTH_USER_AGENT,
        viewport=STEALTH_VIEWPORT,
        extra_http_headers=STEALTH_HEADERS,
    )
    page = await context.new_page()
    page.set_default_timeout(settings.scrape_timeout_ms)

    try:
        yield page
    finally:
        await context.close()


async def scrape_url(
    url: str,
    *,
    wait_until: str = "networkidle",
    selector: str | None = None,
) -> dict[str, Any]:
    async with _page_context() as page:
        response = await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2.0, 4.0))
        if response is None:
            raise RuntimeError(f"Failed to load page: {url}")

        if selector:
            await page.wait_for_selector(selector)

        title = await page.title()
        content = await page.content()

        return {
            "url": page.url,
            "status": response.status,
            "title": title,
            "html": content,
        }


async def close_browser() -> None:
    global _playwright, _browser

    async with _browser_lock:
        if _browser is not None:
            await _browser.close()
            _browser = None
        if _playwright is not None:
            await _playwright.stop()
            _playwright = None
