from pydantic import BaseModel

from app.schemas.common import Rol


class WhoAmIResponse(BaseModel):
    rol: Rol
    cuadrante_asignado: str | None
    # Pre-mortem T5: comandante sin cuadrante → el frontend avisa en vez de mostrar mapa vacío
    cuadrante_pendiente: bool
