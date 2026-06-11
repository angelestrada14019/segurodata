"""POST /predict — nivel de riesgo por UPZ×mes (lookup, cualquier rol autenticado)."""

from fastapi import APIRouter, Depends, Request

from app.dependencies import CurrentUser, get_prediction_service
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["prediccion"])


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: Request,  # requerido por slowapi
    body: PredictRequest,
    user: CurrentUser,
    service: PredictionService = Depends(get_prediction_service),
) -> dict:
    return await service.get_prediction(user, body.upz_cod, body.anio, body.mes)
