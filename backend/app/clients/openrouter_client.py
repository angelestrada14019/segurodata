"""Cliente OpenRouter — proxy LLM server-side (la key JAMÁS llega al frontend).

D6: toda llamada pasa por TTLCache (cuota gratis 1M tokens/día).
Fallback automático al modelo secundario ante 429/5xx.
"""

import httpx
import structlog

from app.config import Settings
from app.core.cache import crear_llm_cache, llm_cache_key
from app.exceptions import UpstreamError

logger = structlog.get_logger("openrouter")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._cache = crear_llm_cache(settings.llm_cache_maxsize, settings.llm_cache_ttl_seconds)
        self._http = httpx.AsyncClient(timeout=30.0)

    @property
    def configurado(self) -> bool:
        return bool(self._settings.openrouter_api_key)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def chat(self, messages: list[dict], model: str | None = None) -> tuple[str, str, bool]:
        """Devuelve (contenido, modelo_usado, cacheado)."""
        modelo = model or self._settings.llm_model
        key = llm_cache_key(modelo, messages)
        if key in self._cache:
            return self._cache[key], modelo, True

        contenido, modelo_usado = await self._llamar_con_fallback(messages, modelo)
        self._cache[key] = contenido
        return contenido, modelo_usado, False

    async def _llamar_con_fallback(self, messages: list[dict], modelo: str) -> tuple[str, str]:
        try:
            return await self._llamar(messages, modelo), modelo
        except UpstreamError as exc:
            fallback = self._settings.llm_model_fallback
            if not fallback or fallback == modelo:
                raise
            logger.warning("llm_fallback", primario=modelo, fallback=fallback, motivo=exc.message)
            return await self._llamar(messages, fallback), fallback

    async def _llamar(self, messages: list[dict], modelo: str) -> str:
        if not self.configurado:
            raise UpstreamError("OPENROUTER_API_KEY no configurada")
        try:
            resp = await self._http.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self._settings.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/angelestrada14019/segurodata",
                    "X-Title": "SeguroData Bogota",
                },
                json={
                    "model": modelo,
                    "messages": messages,
                    "max_tokens": self._settings.llm_max_tokens,
                },
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"OpenRouter inaccesible: {exc}") from exc

        if resp.status_code == 429 or resp.status_code >= 500:
            raise UpstreamError(f"OpenRouter {resp.status_code} con modelo {modelo}")
        if resp.status_code != 200:
            raise UpstreamError(f"OpenRouter {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise UpstreamError("Respuesta OpenRouter sin contenido") from exc
