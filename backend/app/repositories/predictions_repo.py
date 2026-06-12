"""Repositorio de la tabla `predicciones` (lookup por PK — D2: nunca inferencia)."""

from supabase import AsyncClient

from app.exceptions import UpstreamError


class PredictionsRepo:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def get(self, upz_cod: str, anio: int, mes: int) -> dict | None:
        try:
            resp = await (
                self._client.table("predicciones")
                .select(
                    "upz_cod, anio, mes, nivel_riesgo, prob_critico, prob_alto, prob_medio, prob_bajo, origen"
                )
                .eq("upz_cod", upz_cod)
                .eq("anio", anio)
                .eq("mes", mes)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise UpstreamError(f"Supabase predicciones: {exc}") from exc
        return resp.data[0] if resp.data else None
