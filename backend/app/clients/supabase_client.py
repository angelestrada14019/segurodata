"""Cliente Supabase async (D1) — singleton creado en el lifespan.

⚠️ D8: este cliente usa la SERVICE_KEY → bypasea RLS. El filtro por rol/cuadrante
se aplica en la capa services, nunca se delega a RLS desde el backend.
"""

import structlog
from supabase import AsyncClient, acreate_client

from app.config import Settings

logger = structlog.get_logger("supabase")


async def create_supabase(settings: Settings) -> AsyncClient | None:
    if not settings.supabase_url or not settings.supabase_service_key:
        logger.warning("supabase_sin_configurar", detalle="SUPABASE_URL/SERVICE_KEY ausentes")
        return None
    client = await acreate_client(settings.supabase_url, settings.supabase_service_key)
    logger.info("supabase_conectado", url=settings.supabase_url)
    return client
