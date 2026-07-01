"""Repositorio de `user_profiles` — perfil de rol y cuadrante asignado por usuario."""

from supabase import AsyncClient

from app.exceptions import UpstreamError


class UserProfilesRepo:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def asignar_cuadrante(self, user_id: str, cuadrante_id: str) -> bool:
        """Asigna `cuadrante_asignado` al perfil de `user_id`.

        Devuelve True si el UPDATE afectó alguna fila, False si `user_id` no
        existe en `user_profiles` (pre-mortem T5: hoy solo se podía hacer por
        SQL/Dashboard manual).
        """
        try:
            resp = await (
                self._client.table("user_profiles")
                .update({"cuadrante_asignado": cuadrante_id})
                .eq("user_id", user_id)
                .execute()
            )
        except Exception as exc:
            raise UpstreamError(f"Supabase user_profiles: {exc}") from exc
        return bool(resp.data)
