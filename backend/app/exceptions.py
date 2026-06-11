"""Errores de dominio + handlers centralizados.

Los services lanzan estas excepciones; nadie construye JSONResponse a mano.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger("errors")


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = ""):
        self.message = message or self.__class__.__doc__ or "Error interno"
        super().__init__(self.message)


class NotFoundError(AppError):
    """Recurso no encontrado."""

    status_code = 404
    code = "not_found"


class UnauthorizedError(AppError):
    """Token ausente o inválido."""

    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    """El rol del usuario no permite esta operación."""

    status_code = 403
    code = "forbidden"


class UpstreamError(AppError):
    """Fallo en un servicio externo (Supabase / OpenRouter)."""

    status_code = 502
    code = "upstream_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("app_error", code=exc.code, message=exc.message, path=request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "detalle": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "detalle": "Error interno del servidor"},
        )
