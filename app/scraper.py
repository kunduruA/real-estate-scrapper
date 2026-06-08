import asyncio
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, Page, async_playwright

from app.config import get_settings

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
    page = await browser.new_page()
    page.set_default_timeout(settings.scrape_timeout_ms)

    try:
        yield page
    finally:
        await page.close()


async def scrape_url(
    url: str,
    *,
    wait_until: str = "networkidle",
    selector: str | None = None,
) -> dict[str, Any]:
    async with _page_context() as page:
        response = await page.goto(url, wait_until=wait_until)
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
