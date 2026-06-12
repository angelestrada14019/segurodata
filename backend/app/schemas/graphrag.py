from pydantic import BaseModel, Field

from app.schemas.common import UpzCod


class GraphRAGRequest(BaseModel):
    pregunta: str = Field(min_length=5, max_length=500)
    upz_contexto: UpzCod | None = None


class Fuente(BaseModel):
    tipo: str
    titulo: str | None = None
    fecha: str | None = None
    url: str | None = None
    similitud: float | None = None


class GraphRAGResponse(BaseModel):
    respuesta: str
    fuentes: list[Fuente]
    modelo_llm: str
    cacheado: bool
