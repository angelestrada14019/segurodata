from pydantic import BaseModel

from app.schemas.common import Anio, Mes, NivelRiesgo, UpzCod


class PredictRequest(BaseModel):
    upz_cod: UpzCod
    anio: Anio
    mes: Mes


class PredictResponse(BaseModel):
    upz_cod: str
    anio: int
    mes: int
    nivel_riesgo: NivelRiesgo
    probabilidades: dict[NivelRiesgo, float]
    origen: str
