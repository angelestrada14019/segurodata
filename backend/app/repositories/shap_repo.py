"""Repositorio de la tabla `shap_values` (pre-computados — D2: nunca on-demand)."""

from supabase import AsyncClient

from app.exceptions import UpstreamError


class ShapRepo:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_values(self, upz_cod: str, anio: int, mes: int) -> list[dict]:
        """Todas las features del periodo, ordenadas por |valor| descendente."""
        try:
            resp = await (
                self._client.table("shap_values")
                .select("feature, valor")
                .eq("upz_cod", upz_cod)
                .eq("anio", anio)
                .eq("mes", mes)
                .execute()
            )
        except Exception as exc:
            raise UpstreamError(f"Supabase shap_values: {exc}") from exc
        filas = resp.data or []
        return sorted(filas, key=lambda f: abs(f["valor"]), reverse=True)
