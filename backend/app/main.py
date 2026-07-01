"""SeguroData API — factory de la aplicación FastAPI.

Arquitectura en capas: routers → services → repositories → clients.
Recursos compartidos (Supabase, OpenRouter, embeddings, ontología) viven en
app.state y se crean una sola vez en el lifespan.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.clients.embeddings import EmbeddingsClient
from app.clients.openrouter_client import OpenRouterClient
from app.clients.supabase_client import create_supabase
from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.limits import limiter
from app.logging_config import setup_logging
from app.middleware import RequestContextMiddleware
from app.repositories.ontology_repo import OntologyRepo
from app.routers import admin, auth, explain, graphrag, health, predict, prescribe

logger = structlog.get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.supabase = await create_supabase(settings)
    app.state.openrouter = OpenRouterClient(settings)
    # El modelo de embeddings se carga perezosamente en el primer /graphrag
    # (en thread executor) — el healthcheck de Railway no espera a torch.
    app.state.embeddings = EmbeddingsClient(settings)
    app.state.ontology = OntologyRepo(settings.tabla_ontologica_path)
    logger.info("startup", env=settings.env, version=__version__)
    yield
    await app.state.openrouter.aclose()
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.env)

    app = FastAPI(
        title="SeguroData API",
        description="Predicción y prescripción de seguridad ciudadana por UPZ — Bogotá D.C.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)

    # Orden: el último agregado es el más externo (CORS debe envolver todo)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(predict.router)
    app.include_router(explain.router)
    app.include_router(graphrag.router)
    app.include_router(prescribe.router)
    app.include_router(admin.router)
    return app


app = create_app()
