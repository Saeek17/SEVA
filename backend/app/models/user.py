import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime

from app.database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="ADMIN") # ADMIN, AGRONOMIST
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
