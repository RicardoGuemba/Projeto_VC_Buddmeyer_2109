# -*- coding: utf-8 -*-
"""
Sistema de logging estruturado usando structlog.

Dois trilhos de log (especificação REALTEC):
- system.log: app/infra/erros (por que quebrou)
- process_trace.log: eventos/transições do processo (em qual passo quebrou)
"""

import logging
import sys
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Any, Dict
from contextvars import ContextVar

import structlog
from structlog.stdlib import BoundLogger

# Context variable para correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Retorna o correlation ID atual ou gera um novo."""
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Define o correlation ID."""
    correlation_id_var.set(cid)


def new_correlation_id() -> str:
    """Gera e define um novo correlation ID."""
    cid = str(uuid.uuid4())[:8]
    correlation_id_var.set(cid)
    return cid


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    """Adiciona correlation ID ao evento de log."""
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def add_timestamp(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    """Adiciona timestamp ISO 8601 ao evento de log (UTC)."""
    event_dict["ts"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event_dict["timestamp"] = event_dict["ts"]  # alias para compatibilidade
    return event_dict


def add_standard_fields(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    """Garante campos obrigatórios: ts, level, logger, feature, use_case."""
    if "feature" not in event_dict:
        event_dict["feature"] = "unknown"
    if "use_case" not in event_dict:
        event_dict["use_case"] = ""
    return event_dict


class TraceLogFilter(logging.Filter):
    """Filtro: passa apenas logs do logger realtec.trace.* para process_trace.log."""

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "name", "").startswith("realtec.trace")


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    process_trace_log_file: Optional[str] = None,
    json_format: bool = False,
    max_bytes: int = 50_000_000,
    backup_count: int = 10,
) -> None:
    """
    Configura o sistema de logging estruturado com dois trilhos.

    - system.log (log_file): app/infra/erros
    - process_trace.log: eventos/transições do processo (realtec.trace.*)

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para system.log (opcional)
        process_trace_log_file: Caminho para process_trace.log (derivado de log_file se None)
        json_format: Se True, usa formato JSON para console
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Processadores structlog (campos obrigatórios: ts, level, logger, feature, use_case)
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        add_timestamp,
        add_standard_fields,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    handlers: list[logging.Handler] = []

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # System log (app/infra/erros)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        system_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        system_handler.setLevel(log_level)
        system_handler.addFilter(lambda r: not getattr(r, "name", "").startswith("realtec.trace"))
        handlers.append(system_handler)

    # Process trace log (eventos/transições) - apenas realtec.trace.*
    if process_trace_log_file is None and log_file:
        log_dir = Path(log_file).parent
        process_trace_log_file = str(log_dir / "process_trace.log")
    if process_trace_log_file:
        Path(process_trace_log_file).parent.mkdir(parents=True, exist_ok=True)
        trace_handler = RotatingFileHandler(
            process_trace_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        trace_handler.setLevel(log_level)
        trace_handler.addFilter(TraceLogFilter())
        handlers.append(trace_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format="%(message)s",
    )

    if json_format:
        console_processor = structlog.processors.JSONRenderer()
    else:
        console_processor = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=console_processor,
        foreign_pre_chain=shared_processors,
    )
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    for i, h in enumerate(handlers):
        if i == 0:
            h.setFormatter(formatter)
        else:
            h.setFormatter(json_formatter)


def get_logger(name: str) -> BoundLogger:
    """
    Retorna um logger estruturado para o componente especificado.
    Logs vão para system.log (app/infra/erros).
    """
    return structlog.get_logger(name)


def get_trace_logger(feature: str, use_case: str = "") -> BoundLogger:
    """
    Retorna logger para process_trace.log (eventos/transições).
    Use para: VISION.CONNECTED, PLC.TAG_WRITE, ROBOT.HANDSHAKE_STEP, etc.
    """
    name = f"realtec.trace.{feature}"
    return structlog.get_logger(name).bind(feature=feature, use_case=use_case)


def trace_event(
    event: str,
    feature: str,
    use_case: str = "",
    cycle_id: str = "",
    frame_id: int = 0,
    state_from: str = "",
    state_to: str = "",
    error_code: str = "",
    duration_ms: float = 0,
    **kwargs: Any,
) -> None:
    """
    Registra evento no process_trace.log.
    Eventos padronizados: VISION.CONNECTED, PLC.TAG_WRITE, ROBOT.HANDSHAKE_STEP, etc.
    """
    logger = get_trace_logger(feature, use_case)
    payload: Dict[str, Any] = {"event": event, "message": event, **kwargs}
    if cycle_id:
        payload["cycle_id"] = cycle_id
    if frame_id:
        payload["frame_id"] = frame_id
    if state_from:
        payload["state_from"] = state_from
    if state_to:
        payload["state_to"] = state_to
    if error_code:
        payload["error_code"] = error_code
    if duration_ms:
        payload["duration_ms"] = duration_ms
    extra = {k: v for k, v in payload.items() if k not in ("event", "message")}
    logger.info(event, **extra)


# Loggers pré-configurados para componentes principais
class Loggers:
    """Container para loggers dos componentes principais."""
    
    @staticmethod
    def app() -> BoundLogger:
        return get_logger("app")
    
    @staticmethod
    def streaming() -> BoundLogger:
        return get_logger("streaming")
    
    @staticmethod
    def detection() -> BoundLogger:
        return get_logger("detection")
    
    @staticmethod
    def cip() -> BoundLogger:
        return get_logger("cip")
    
    @staticmethod
    def control() -> BoundLogger:
        return get_logger("control")
    
    @staticmethod
    def ui() -> BoundLogger:
        return get_logger("ui")
