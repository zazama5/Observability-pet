import logging
import json
import socket
from datetime import datetime, timezone
from config import settings


class JSONFormatter(logging.Formatter):
    """JSON-форматтер для stdout с полем log_stream для маршрутизации."""

    def __init__(self, log_stream: str):
        super().__init__()
        self.log_stream = log_stream
        self.instance_id = settings.instance_id or socket.gethostname() or "local-dev"

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "log_stream": self.log_stream,
            "message": record.getMessage(),
            "instance_id": self.instance_id,
            "service": "auth-service",
        }

        for key in ("username", "ip", "user_agent", "success",
                     "event_type", "method", "path", "status_code",
                     "duration_ms", "status"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    app_handler = logging.StreamHandler()
    app_handler.setFormatter(JSONFormatter(log_stream="app"))
    app_logger.addHandler(app_handler)

    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False

    audit_handler = logging.StreamHandler()
    audit_handler.setFormatter(JSONFormatter(log_stream="audit"))
    audit_logger.addHandler(audit_handler)

    return app_logger, audit_logger


app_logger, audit_logger = setup_logging()


def log_audit(event_type: str, username: str, ip: str, user_agent: str, success: bool):
    audit_logger.info(
        "audit_event",
        extra={
            "event_type": event_type,
            "username": username,
            "ip": ip,
            "user_agent": user_agent,
            "success": success,
        }
    )