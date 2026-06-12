from pydantic import BaseModel

from app.schemas.common import NivelRiesgo, ShapFeature


class ExplainResponse(BaseModel):
    upz_cod: str
    anio: int
    mes: int
    nivel_riesgo: NivelRiesgo
    shap_top3: list[ShapFeature]
    # Solo ANALISTA_SDSCJ / ADMIN reciben el detalle completo (matriz endpoint×rol)
    shap_completo: list[ShapFeature] | None = None
