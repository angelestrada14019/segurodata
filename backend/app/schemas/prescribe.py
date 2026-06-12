from pydantic import BaseModel, Field

from app.schemas.common import ShapFeature, UpzCod


class PrescribeRequest(BaseModel):
    upz_cod: UpzCod
    shap_top: list[ShapFeature] = Field(min_length=1, max_length=5)


class Diagnostico(BaseModel):
    feature: str
    diagnostico: str
    tipo_intervencion: str
    entidad_responsable: str
    accion: str


class CaiInfo(BaseModel):
    cuadrante_id: str
    nombre: str
    telefono: str | None = None


class PrescribeResponse(BaseModel):
    upz_cod: str
    diagnosticos: list[Diagnostico]
    cai: CaiInfo | None = None
    recomendacion_llm: str
    modelo_llm: str | None = None
