"""Inyección de dependencias FastAPI — la única fábrica de repos/services/claims."""

from typing import Annotated

import structlog
from fastapi import Depends, Header, Request

from app.clients.embeddings import EmbeddingsClient
from app.clients.openrouter_client import OpenRouterClient
from app.config import Settings, get_settings
from app.core.security import UserClaims, decode_supabase_jwt
from app.exceptions import ForbiddenError, UnauthorizedError, UpstreamError
from app.repositories.cuadrantes_repo import CuadrantesRepo
from app.repositories.documents_repo import DocumentsRepo
from app.repositories.ontology_repo import OntologyRepo
from app.repositories.predictions_repo import PredictionsRepo
from app.repositories.shap_repo import ShapRepo
from app.services.explain_service import ExplainService
from app.services.graphrag_service import GraphRAGService
from app.services.prediction_service import PredictionService
from app.services.prescribe_service import PrescribeService

logger = structlog.get_logger("deps")

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Clients (singletons en app.state, creados en el lifespan) ──────────────


def get_supabase(request: Request):
    client = getattr(request.app.state, "supabase", None)
    if client is None:
        raise UpstreamError("Supabase no configurado (SUPABASE_URL/SERVICE_KEY)")
    return client


def get_openrouter(request: Request) -> OpenRouterClient:
    return request.app.state.openrouter


def get_embeddings(request: Request) -> EmbeddingsClient:
    return request.app.state.embeddings


def get_ontology(request: Request) -> OntologyRepo:
    return request.app.state.ontology


# ── Repositories ────────────────────────────────────────────────────────────


def get_predictions_repo(client=Depends(get_supabase)) -> PredictionsRepo:
    return PredictionsRepo(client)


def get_shap_repo(client=Depends(get_supabase)) -> ShapRepo:
    return ShapRepo(client)


def get_cuadrantes_repo(client=Depends(get_supabase)) -> CuadrantesRepo:
    return CuadrantesRepo(client)


def get_documents_repo(client=Depends(get_supabase)) -> DocumentsRepo:
    return DocumentsRepo(client)


# ── Services ────────────────────────────────────────────────────────────────


def get_prediction_service(
    predictions: PredictionsRepo = Depends(get_predictions_repo),
    cuadrantes: CuadrantesRepo = Depends(get_cuadrantes_repo),
) -> PredictionService:
    return PredictionService(predictions, cuadrantes)


def get_explain_service(
    shap: ShapRepo = Depends(get_shap_repo),
    predictions: PredictionsRepo = Depends(get_predictions_repo),
    cuadrantes: CuadrantesRepo = Depends(get_cuadrantes_repo),
) -> ExplainService:
    return ExplainService(shap, predictions, cuadrantes)


def get_graphrag_service(
    embeddings: EmbeddingsClient = Depends(get_embeddings),
    documents: DocumentsRepo = Depends(get_documents_repo),
    openrouter: OpenRouterClient = Depends(get_openrouter),
) -> GraphRAGService:
    return GraphRAGService(embeddings, documents, openrouter)


def get_prescribe_service(
    ontology: OntologyRepo = Depends(get_ontology),
    cuadrantes: CuadrantesRepo = Depends(get_cuadrantes_repo),
    openrouter: OpenRouterClient = Depends(get_openrouter),
) -> PrescribeService:
    return PrescribeService(ontology, cuadrantes, openrouter)


# ── Auth ────────────────────────────────────────────────────────────────────

_USUARIO_DEV = UserClaims(
    sub="dev-admin",
    email="dev@segurodata.local",
    rol="ADMIN",
    cuadrante_asignado=None,
    rol_desde_claims=True,
)


async def get_current_user(
    request: Request,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> UserClaims:
    # AUTH_MODE=disabled SOLO en development (guard adicional al de Settings)
    if settings.auth_mode == "disabled":
        if settings.env != "development":
            raise UnauthorizedError("AUTH_MODE=disabled fuera de development")
        return _USUARIO_DEV

    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Falta el header Authorization: Bearer <token>")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_supabase_jwt(token, settings.supabase_jwt_secret, settings.supabase_jwks_url)

    # Resiliencia: si el custom_access_token_hook aún no está habilitado, el token
    # no trae `rol` — caemos al perfil en DB para no degradar a todos a CIUDADANO.
    if not claims.rol_desde_claims:
        supabase = getattr(request.app.state, "supabase", None)
        if supabase is not None and claims.sub:
            try:
                resp = await (
                    supabase.table("user_profiles")
                    .select("rol, cuadrante_asignado")
                    .eq("user_id", claims.sub)
                    .limit(1)
                    .execute()
                )
                if resp.data:
                    perfil = resp.data[0]
                    claims = UserClaims(
                        sub=claims.sub,
                        email=claims.email,
                        rol=perfil["rol"],
                        cuadrante_asignado=perfil.get("cuadrante_asignado"),
                        rol_desde_claims=False,
                    )
            except Exception:
                logger.warning("fallback_perfil_fallo", sub=claims.sub)
    return claims


CurrentUser = Annotated[UserClaims, Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependencia de autorización por rol — 403 si el rol no está permitido."""

    async def _verificar(user: CurrentUser) -> UserClaims:
        if user.rol not in roles:
            raise ForbiddenError(f"El rol {user.rol} no tiene acceso a este recurso")
        return user

    return Depends(_verificar)
