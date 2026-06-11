"""Repositorio de `cuadrantes_geom` — mapeo cuadrante↔UPZs y datos del CAI (F4)."""

from supabase import AsyncClient

from app.exceptions import UpstreamError


class CuadrantesRepo:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def get_upzs(self, cuadrante_id: str) -> list[str]:
        """UPZs cubiertas por un cuadrante — base del filtro D8 para COMANDANTE_CAI."""
        try:
            resp = await (
                self._client.table("cuadrantes_geom")
                .select("upz_codes")
                .eq("cuadrante_id", cuadrante_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise UpstreamError(f"Supabase cuadrantes_geom: {exc}") from exc
        if not resp.data:
            return []
        return resp.data[0].get("upz_codes") or []

    async def find_cai_para_upz(self, upz_cod: str) -> dict | None:
        """Primer CAI cuyo cuadrante cubre la UPZ (para /prescribe)."""
        try:
            resp = await (
                self._client.table("cuadrantes_geom")
                .select("cuadrante_id, nom_cai, telefono")
                .contains("upz_codes", [upz_cod])
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise UpstreamError(f"Supabase cuadrantes_geom: {exc}") from exc
        return resp.data[0] if resp.data else None
