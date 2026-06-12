"""Rate limiting (D5) — slowapi in-memory (Railway corre 1 sola instancia).

Default 60/min por IP en todos los endpoints; /graphrag y /prescribe bajan a
10/min (protegen la cuota gratis de OpenRouter); /health queda exento.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def _limite_default() -> str:
    return get_settings().rate_limit_default


def limite_llm() -> str:
    return get_settings().rate_limit_llm


limiter = Limiter(key_func=get_remote_address, default_limits=[_limite_default])
