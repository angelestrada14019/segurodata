"""Lógica de /graphrag — embed → retrieval pgvector → OpenRouter con citas.

Flujo (presupuesto <2s): embed ~50ms + RPC ~150ms + Gemini Flash ~1.5s.
Si el filtro por UPZ da 0 resultados, reintenta sin filtro (nunca respuesta vacía).
"""

import structlog

from app.clients.embeddings import EmbeddingsClient
from app.clients.openrouter_client import OpenRouterClient
from app.exceptions import UpstreamError
from app.repositories.documents_repo import DocumentsRepo

logger = structlog.get_logger("graphrag")

SYSTEM_PROMPT = (
    "Eres el analista causal de SeguroData Bogotá. Respondes en español, en lenguaje "
    "operacional claro (para un comandante de CAI, sin jerga de machine learning). "
    "Usa EXCLUSIVAMENTE los fragmentos del corpus que se te entregan, citando cada "
    "afirmación con su número [n]. El corpus es pequeño y en su mayoría noticias "
    "generales de Bogotá, no siempre específicas de la zona consultada — si los "
    "fragmentos hablan de la ciudad en general pero no mencionan la zona, dilo así "
    "explícitamente ('no hay noticias específicas de esta zona, pero el contexto "
    "general de Bogotá es: ...') en vez de decir que no tienes información y luego "
    "citar igual. Solo di 'No tengo información en el corpus sobre esto' cuando "
    "ningún fragmento tenga relación alguna con el tema de la pregunta. Máximo 250 "
    "palabras."
)


class GraphRAGService:
    def __init__(
        self,
        embeddings: EmbeddingsClient,
        documents: DocumentsRepo,
        openrouter: OpenRouterClient,
    ):
        self._embeddings = embeddings
        self._documents = documents
        self._openrouter = openrouter

    async def answer(
        self,
        pregunta: str,
        upz_contexto: str | None = None,
        upz_nombre: str | None = None,
        nom_localidad: str | None = None,
    ) -> dict:
        vector = await self._embeddings.encode(pregunta)

        chunks = await self._documents.match(
            vector, threshold=0.7, count=5, filter_upz=upz_contexto
        )
        if not chunks and upz_contexto:
            logger.info("retrieval_retry_sin_filtro", upz=upz_contexto)
            chunks = await self._documents.match(vector, threshold=0.7, count=5, filter_upz=None)
        if not chunks:
            # Umbral relajado como último intento antes de declarar corpus insuficiente
            chunks = await self._documents.match(vector, threshold=0.5, count=5, filter_upz=None)

        fuentes = [
            {
                "tipo": c.get("source", "DESCONOCIDO"),
                "titulo": c.get("titulo"),
                "fecha": str(c["fecha"]) if c.get("fecha") else None,
                "url": c.get("url"),
                "similitud": round(c["similarity"], 3) if c.get("similarity") is not None else None,
            }
            for c in chunks
        ]

        if not chunks:
            return {
                "respuesta": "No tengo información en el corpus sobre esto. "
                "El corpus se amplía con cada noticia nueva indexada.",
                "fuentes": [],
                "modelo_llm": "ninguno",
                "cacheado": False,
            }

        contexto = "\n\n".join(
            f"[{i + 1}] ({c.get('source', '?')}, {c.get('fecha', 's.f.')}) {c['content']}"
            for i, c in enumerate(chunks)
        )
        user_msg = f"Fragmentos del corpus:\n{contexto}\n\nPregunta: {pregunta}"
        if upz_contexto:
            zona = f"UPZ {upz_contexto}"
            if upz_nombre:
                zona += f" ({upz_nombre}"
                zona += f", localidad {nom_localidad})" if nom_localidad else ")"
            user_msg += f"\n(Contexto: {zona} de Bogotá)"

        try:
            respuesta, modelo, cacheado = await self._openrouter.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ]
            )
        except UpstreamError as exc:
            # Degradación elegante: el retrieval sigue siendo útil sin LLM
            logger.warning("graphrag_sin_llm", motivo=exc.message)
            respuesta = (
                "(LLM no disponible — mostrando fragmentos relevantes del corpus)\n\n"
                + "\n\n".join(f"[{i + 1}] {c['content'][:300]}" for i, c in enumerate(chunks[:3]))
            )
            modelo, cacheado = "ninguno", False

        return {
            "respuesta": respuesta,
            "fuentes": fuentes,
            "modelo_llm": modelo,
            "cacheado": cacheado,
        }
