"""Lógica de /explain — SHAP pre-computado, nivel de detalle según rol."""

from app.core.security import UserClaims
from app.exceptions import NotFoundError
from app.repositories.cuadrantes_repo import CuadrantesRepo
from app.repositories.predictions_repo import PredictionsRepo
from app.repositories.shap_repo import ShapRepo
from app.services.prediction_service import verificar_acceso_upz

ROLES_DETALLE_COMPLETO = {"ANALISTA_SDSCJ", "ADMIN"}


class ExplainService:
    def __init__(self, shap: ShapRepo, predictions: PredictionsRepo, cuadrantes: CuadrantesRepo):
        self._shap = shap
        self._predictions = predictions
        self._cuadrantes = cuadrantes

    async def get_explanation(self, claims: UserClaims, upz_cod: str, anio: int, mes: int) -> dict:
        await verificar_acceso_upz(claims, upz_cod, self._cuadrantes)
        prediccion = await self._predictions.get(upz_cod, anio, mes)
        if prediccion is None:
            raise NotFoundError(f"Sin predicción para UPZ {upz_cod} en {anio}-{mes:02d}")
        valores = await self._shap.get_values(upz_cod, anio, mes)
        if not valores:
            raise NotFoundError(f"Sin SHAP values para UPZ {upz_cod} en {anio}-{mes:02d}")

        respuesta = {
            "upz_cod": upz_cod,
            "anio": anio,
            "mes": mes,
            "nivel_riesgo": prediccion["nivel_riesgo"],
            "shap_top3": valores[:3],
        }
        if claims.rol in ROLES_DETALLE_COMPLETO:
            respuesta["shap_completo"] = valores
        return respuesta
