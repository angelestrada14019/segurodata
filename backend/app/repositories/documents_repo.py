"""Repositorio del corpus GraphRAG — RPC match_documents (pgvector HNSW, D9)."""

from supabase import AsyncClient

from app.exceptions import UpstreamError


class DocumentsRepo:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def match(
        self,
        embedding: list[float],
        threshold: float = 0.7,
        count: int = 5,
        filter_upz: str | None = None,
    ) -> list[dict]:
        try:
            resp = await self._client.rpc(
                "match_documents",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": count,
                    "filter_upz": filter_upz,
                },
            ).execute()
        except Exception as exc:
            raise UpstreamError(f"Supabase match_documents: {exc}") from exc
        return resp.data or []
