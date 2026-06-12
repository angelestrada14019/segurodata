"""Logging estructurado JSON con structlog — Railway parsea JSON nativamente."""

import logging
import sys

import structlog


def setup_logging(env: str) -> None:
    nivel = logging.DEBUG if env == "development" else logging.INFO
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=nivel)

    renderer = (
        structlog.dev.ConsoleRenderer()
        if env == "development"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(nivel),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
