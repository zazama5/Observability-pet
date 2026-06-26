from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres: хранит users и audit-логи
    database_url: str = "postgresql+psycopg2://auth:auth@localhost:5432/auth"

    # JWT
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900       # 15 минут
    refresh_token_ttl_seconds: int = 604800   # 7 дней

    # путь для audit-лога (его подхватывает Vector-agent)
    audit_log_path: str = "/var/log/auth/audit.log"

    # имя пода/инстанса — пишется в app-логи, чтобы видеть балансировку nginx
    instance_id: str = "local"

    class Config:
        env_prefix = ""  # читаем DATABASE_URL, JWT_SECRET и т.д.


settings = Settings()
