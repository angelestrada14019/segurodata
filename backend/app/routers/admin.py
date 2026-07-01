"""PATCH /admin/usuarios/{user_id}/cuadrante — asigna cuadrante (solo ADMIN).

Cierra el pre-mortem T5: hoy `user_profiles.cuadrante_asignado` solo se podía
tocar por SQL/Dashboard manual.
"""

from fastapi import APIRouter, Depends, Request

from app.core.security import UserClaims
from app.dependencies import get_admin_service, require_roles
from app.schemas.admin import AsignarCuadranteRequest, AsignarCuadranteResponse
from app.services.admin_service import AdminService

router = APIRouter(tags=["admin"])


@router.patch("/admin/usuarios/{user_id}/cuadrante", response_model=AsignarCuadranteResponse)
async def asignar_cuadrante(
    request: Request,  # requerido por slowapi
    user_id: str,
    body: AsignarCuadranteRequest,
    admin: UserClaims = require_roles("ADMIN"),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    return await service.asignar_cuadrante(admin, user_id, body.cuadrante_id)
