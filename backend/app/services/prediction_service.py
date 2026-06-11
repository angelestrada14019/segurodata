"""Lógica de /predict — lookup + enforcement de rol (D8).

D8: el cliente Supabase del backend usa la service key (bypasea RLS), por lo
que el filtro comandante-por-cuadrante se aplica AQUÍ, explícitamente.
"""

from app.core.security import UserClaims
from app.exceptions import ForbiddenError, NotFoundError
from app.repositories.cuadrantes_repo import CuadrantesRepo
from app.repositories.predictions_repo import PredictionsRepo


async def verificar_acceso_upz(
    claims: UserClaims, upz_cod: str, cuadrantes: CuadrantesRepo
) -> None:
    """COMANDANTE_CAI solo accede a UPZs de su cuadrante asignado (403 fuera)."""
    if claims.rol != "COMANDANTE_CAI":
        return
    if not claims.cuadrante_asignado:
        raise ForbiddenError(
            "Comandante sin cuadrante asignado — un ADMIN debe asignarlo (ver /whoami)"
        )
    upzs = await cuadrantes.get_upzs(claims.cuadrante_asignado)
    if upz_cod not in upzs:
        raise ForbiddenError(
            f"La UPZ {upz_cod} está fuera del cuadrante asignado {claims.cuadrante_asignado}"
        )


class PredictionService:
    def __init__(self, predictions: PredictionsRepo, cuadrantes: CuadrantesRepo):
        self._predictions = predictions
        self._cuadrantes = cuadrantes

    async def get_prediction(self, claims: UserClaims, upz_cod: str, anio: int, mes: int) -> dict:
        await verificar_acceso_upz(claims, upz_cod, self._cuadrantes)
        fila = await self._predictions.get(upz_cod, anio, mes)
        if fila is None:
            raise NotFoundError(f"Sin predicción para UPZ {upz_cod} en {anio}-{mes:02d}")
        return {
            "upz_cod": fila["upz_cod"],
            "anio": fila["anio"],
            "mes": fila["mes"],
            "nivel_riesgo": fila["nivel_riesgo"],
            "probabilidades": {
                "CRITICO": fila["prob_critico"],
                "ALTO": fila["prob_alto"],
                "MEDIO": fila["prob_medio"],
                "BAJO": fila["prob_bajo"],
            },
            "origen": fila["origen"],
        }
