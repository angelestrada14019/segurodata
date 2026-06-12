"""GET /explain — SHAP pre-computado (top-3; completo para ANALISTA/ADMIN)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import CurrentUser, get_explain_service
from app.schemas.explain import ExplainResponse
from app.services.explain_service import ExplainService

router = APIRouter(tags=["prediccion"])


@router.get("/explain", response_model=ExplainResponse, response_model_exclude_none=True)
async def explain(
    request: Request,
    user: CurrentUser,
    upz_cod: Annotated[str, Query(pattern=r"^\d{3}$")],
    anio: Annotated[int, Query(ge=2020, le=2030)],
    mes: Annotated[int, Query(ge=1, le=12)],
    service: ExplainService = Depends(get_explain_service),
) -> dict:
    return await service.get_explanation(user, upz_cod, anio, mes)
