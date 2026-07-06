import logging
import sys

try:
    import structlog
except ModuleNotFoundError:  # pragma: no cover - exercised in lightweight local test envs
    structlog = None

from shared.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    if structlog is not None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(),
        )


def get_logger(name: str):
    if structlog is not None:
        return structlog.get_logger(name)
    return logging.getLogger(name)
