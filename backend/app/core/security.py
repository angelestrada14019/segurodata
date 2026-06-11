"""Verificación de JWT de Supabase Auth (D7: PyJWT HS256 + claims custom).

Claims custom `rol` y `cuadrante_asignado` los inyecta el custom_access_token_hook
de Supabase. Si el hook aún no está habilitado, `rol` cae a CIUDADANO — el
fallback a user_profiles lo resuelve la capa de dependencias, no este módulo.
"""

from dataclasses import dataclass
from typing import Literal

import jwt

from app.exceptions import UnauthorizedError

Rol = Literal["CIUDADANO", "COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"]
ROLES_VALIDOS = {"CIUDADANO", "COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"}


@dataclass(frozen=True)
class UserClaims:
    sub: str
    email: str
    rol: str
    cuadrante_asignado: str | None
    rol_desde_claims: bool  # False => el token no traía rol (hook no habilitado)

    @property
    def cuadrante_pendiente(self) -> bool:
        return self.rol == "COMANDANTE_CAI" and not self.cuadrante_asignado


def decode_supabase_jwt(token: str, secret: str, jwks_url: str = "") -> UserClaims:
    if not token:
        raise UnauthorizedError("Falta el token de autenticación")
    try:
        if jwks_url:
            # Escape hatch: proyecto con llaves asimétricas (ES256/RS256)
            client = jwt.PyJWKClient(jwks_url)
            key = client.get_signing_key_from_jwt(token).key
            payload = jwt.decode(
                token, key, algorithms=["ES256", "RS256"], audience="authenticated"
            )
        else:
            payload = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(f"Token inválido: {exc}") from exc

    rol = payload.get("rol")
    rol_desde_claims = rol in ROLES_VALIDOS
    if not rol_desde_claims:
        rol = "CIUDADANO"
    cuadrante = payload.get("cuadrante_asignado") or None
    return UserClaims(
        sub=payload.get("sub", ""),
        email=payload.get("email", ""),
        rol=rol,
        cuadrante_asignado=cuadrante,
        rol_desde_claims=rol_desde_claims,
    )
