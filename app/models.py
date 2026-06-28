from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from db import Base

class User(Base):
    __tablename__ = "users"  # <-- Обязательно двойные подчеркивания!
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Класс AuditEvent удален, так как мы больше не пишем аудит в базу данных.
