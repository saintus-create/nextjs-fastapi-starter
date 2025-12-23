"""Structured logging configuration using structlog."""
from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(level: str = "INFO", renderer: str = "console") -> None:
    """Configure structlog with the specified level and renderer.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        renderer: Output format - 'console' for dev, 'json' for production
    """
    # Set up standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # Choose renderer
    if renderer == "json":
        renderer_processor = structlog.processors.JSONRenderer()
    else:
        renderer_processor = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer_processor,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
