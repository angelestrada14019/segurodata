"""Middleware de contexto: request_id + access log con latencia."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger("access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
        structlog.contextvars.bind_contextvars(request_id=request_id)
        inicio = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        ms = (time.perf_counter() - inicio) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round(ms, 1),
            request_id=request_id,
        )
        return response
