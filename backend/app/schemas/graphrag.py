from pydantic import BaseModel, Field

from app.schemas.common import UpzCod


class GraphRAGRequest(BaseModel):
    pregunta: str = Field(min_length=5, max_length=500)
    upz_contexto: UpzCod | None = None
    # Nombre/localidad de la UPZ (el frontend ya los tiene en memoria desde
    # useUpzGeometrias() — evita un lookup nuevo en el backend). Solo se usan
    # para enriquecer el prompt del LLM; el filtro de retrieval sigue siendo
    # upz_contexto (el código, columna real de documents_corpus).
    upz_nombre: str | None = Field(default=None, max_length=100)
    nom_localidad: str | None = Field(default=None, max_length=100)


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
