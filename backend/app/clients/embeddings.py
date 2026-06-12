"""Cliente de embeddings — all-MiniLM-L6-v2, 384 dims (D4).

NUNCA cambiar de modelo sin reindexar documents_corpus completo: el índice
pgvector quedaría incompatible.

Dos backends intercambiables vía env EMBEDDINGS_BACKEND (mismo modelo MiniLM):
  - sentence-transformers (default prod, torch CPU horneado en Docker)
  - fastembed (ONNX, ~100MB RAM — dev local y plan B si Railway aprieta)

Carga perezosa en thread executor: el event loop nunca se bloquea.
"""

import asyncio
import threading

import structlog

from app.config import Settings
from app.exceptions import UpstreamError

logger = structlog.get_logger("embeddings")

DIMS = 384


class EmbeddingsClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._model = None
        self._lock = threading.Lock()

    def _cargar(self) -> None:
        """Carga el modelo (una sola vez, thread-safe). Corre en executor."""
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            backend = self._settings.embeddings_backend
            logger.info(
                "embeddings_cargando", backend=backend, modelo=self._settings.embeddings_model
            )
            if backend == "fastembed":
                from fastembed import TextEmbedding

                self._model = ("fastembed", TextEmbedding(self._settings.embeddings_model))
            else:
                from sentence_transformers import SentenceTransformer

                self._model = ("st", SentenceTransformer(self._settings.embeddings_model))
            logger.info("embeddings_listo", backend=backend)

    def _encode_sync(self, texto: str) -> list[float]:
        self._cargar()
        kind, model = self._model
        if kind == "fastembed":
            vec = next(iter(model.embed([texto])))
            return [float(x) for x in vec]
        vec = model.encode(texto, normalize_embeddings=True)
        return [float(x) for x in vec]

    async def encode(self, texto: str) -> list[float]:
        try:
            loop = asyncio.get_running_loop()
            vec = await loop.run_in_executor(None, self._encode_sync, texto)
        except UpstreamError:
            raise
        except Exception as exc:  # modelo no instalado / sin descarga
            raise UpstreamError(f"Embeddings no disponibles: {exc}") from exc
        if len(vec) != DIMS:
            raise UpstreamError(f"Embedding de {len(vec)} dims — se esperaban {DIMS}")
        return vec
