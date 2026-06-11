"""Caché TTL in-process para respuestas LLM (D6) — protege la cuota de OpenRouter."""

import hashlib
import json

from cachetools import TTLCache


def crear_llm_cache(maxsize: int, ttl: int) -> TTLCache:
    return TTLCache(maxsize=maxsize, ttl=ttl)


def llm_cache_key(model: str, messages: list[dict]) -> str:
    raw = model + json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
