from pydantic import BaseModel


class AsignarCuadranteRequest(BaseModel):
    cuadrante_id: str


class AsignarCuadranteResponse(BaseModel):
    user_id: str
    cuadrante_asignado: str
