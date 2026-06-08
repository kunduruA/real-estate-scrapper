from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel, Field, HttpUrl

from app.middleware import RapidApiSecretMiddleware
from app.scraper import close_browser, scrape_url


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_browser()


app = FastAPI(
    title="Lambda Playwright Scraper",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(RapidApiSecretMiddleware)


class ScrapeRequest(BaseModel):
    url: HttpUrl
    wait_until: Literal["load", "domcontentloaded", "networkidle", "commit"] = (
        "networkidle"
    )
    selector: str | None = Field(
        default=None,
        description="Optional CSS selector to wait for before returning HTML.",
    )


class ScrapeResponse(BaseModel):
    url: str
    status: int
    title: str
    html: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(payload: ScrapeRequest) -> ScrapeResponse:
    try:
        result = await scrape_url(
            str(payload.url),
            wait_until=payload.wait_until,
            selector=payload.selector,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ScrapeResponse(**result)


handler = Mangum(app, lifespan="off")
