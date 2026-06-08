import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

RAPIDAPI_PROXY_SECRET_HEADER = "X-RapidAPI-proxy-secret"


class RapidApiSecretMiddleware(BaseHTTPMiddleware):
    """Reject requests that do not present the expected RapidAPI proxy secret."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        settings = get_settings()
        expected_secret = settings.rapid_secret

        if not expected_secret:
            return JSONResponse(
                status_code=500,
                content={"detail": "RAPID_SECRET is not configured"},
            )

        provided_secret = request.headers.get(RAPIDAPI_PROXY_SECRET_HEADER)
        if not provided_secret or not secrets.compare_digest(
            provided_secret, expected_secret
        ):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing RapidAPI proxy secret"},
            )

        return await call_next(request)
