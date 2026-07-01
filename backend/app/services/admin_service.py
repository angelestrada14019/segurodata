"""Lógica de /admin/usuarios/{user_id}/cuadrante — pre-mortem T5.

Hoy `user_profiles.cuadrante_asignado` solo se puede tocar por SQL/Dashboard
manual. Este servicio permite a un ADMIN asignarlo vía API — el frontend
podrá pasar `/whoami.cuadrante_pendiente` de True a False sin intervención manual.
"""

import structlog

from app.core.security import UserClaims
from app.exceptions import NotFoundError
from app.repositories.cuadrantes_repo import CuadrantesRepo
from app.repositories.user_profiles_repo import UserProfilesRepo

logger = structlog.get_logger("admin")


class AdminService:
    def __init__(self, user_profiles: UserProfilesRepo, cuadrantes: CuadrantesRepo):
        self._user_profiles = user_profiles
        self._cuadrantes = cuadrantes

    async def asignar_cuadrante(self, admin: UserClaims, user_id: str, cuadrante_id: str) -> dict:
        upzs = await self._cuadrantes.get_upzs(cuadrante_id)
        if not upzs:
            raise NotFoundError(f"El cuadrante {cuadrante_id} no existe en cuadrantes_geom")

        afectado = await self._user_profiles.asignar_cuadrante(user_id, cuadrante_id)
        if not afectado:
            raise NotFoundError(f"El usuario {user_id} no existe en user_profiles")

        logger.info(
            "cuadrante_asignado",
            admin=admin.sub,
            user_id=user_id,
            cuadrante_id=cuadrante_id,
        )
        return {"user_id": user_id, "cuadrante_asignado": cuadrante_id}
