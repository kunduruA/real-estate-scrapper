from typing import Literal

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel, Field, HttpUrl

from app.middleware import RapidApiSecretMiddleware
from app.scraper import scrape_url

app = FastAPI(
    title="Lambda Crawlbase Scraper",
    version="2.0.0",
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
