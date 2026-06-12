"""Tipos compartidos del contrato (skill backend-segurodata)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

NivelRiesgo = Literal["CRITICO", "ALTO", "MEDIO", "BAJO"]
Rol = Literal["CIUDADANO", "COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"]

UpzCod = Annotated[str, Field(pattern=r"^\d{3}$", description="Código UPZ de 3 dígitos, ej. '044'")]
Anio = Annotated[int, Field(ge=2020, le=2030)]
Mes = Annotated[int, Field(ge=1, le=12)]


class ErrorResponse(BaseModel):
    error: str
    detalle: str


class ShapFeature(BaseModel):
    feature: str
    valor: float
