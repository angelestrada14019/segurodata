"""POST /graphrag — chatbot causal con citas (rate limit 10/min: protege OpenRouter)."""

from fastapi import APIRouter, Depends, Request

from app.dependencies import CurrentUser, get_graphrag_service
from app.limits import limite_llm, limiter
from app.schemas.graphrag import GraphRAGRequest, GraphRAGResponse
from app.services.graphrag_service import GraphRAGService

router = APIRouter(tags=["graphrag"])


@router.post("/graphrag", response_model=GraphRAGResponse)
@limiter.limit(limite_llm)
async def graphrag(
    request: Request,
    body: GraphRAGRequest,
    user: CurrentUser,
    service: GraphRAGService = Depends(get_graphrag_service),
) -> dict:
    return await service.answer(body.pregunta, body.upz_contexto)
