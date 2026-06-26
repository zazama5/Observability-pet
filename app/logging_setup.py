import logging
import os

from pythonjsonlogger import jsonlogger

from .config import settings


def setup_logging():
    """
    Два логгера:
      - 'app'   -> stdout (JSON). Подхватывает Vector-agent (DaemonSet),
                   шумный поток HTTP/latency/ошибок -> Kafka topic app-logs -> Elasticsearch.
      - 'audit' -> файл audit.log (JSON). Security-события.
                   Vector читает файл -> Kafka topic audit-logs -> PostgreSQL.
    """
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # app-логгер -> stdout
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    app_logger.addHandler(stream)

    # audit-логгер -> файл
    os.makedirs(os.path.dirname(settings.audit_log_path), exist_ok=True)
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(settings.audit_log_path)
    file_handler.setFormatter(fmt)
    audit_logger.addHandler(file_handler)

    return app_logger, audit_logger


app_logger, audit_logger = setup_logging()


def log_audit(event_type: str, username: str | None, ip: str | None,
              user_agent: str | None, success: bool):
    audit_logger.info(
        "audit_event",
        extra={
            "event_type": event_type,
            "username": username,
            "ip": ip,
            "user_agent": user_agent,
            "success": success,
        },
    )
