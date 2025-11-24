"""User model for database storage."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    picture = Column(Text, nullable=True)  # URL to profile picture
    role = Column(String, default="user", nullable=False)  # 'admin' or 'user'
    is_active = Column(Boolean, default=False, nullable=False)  # New users are inactive by default
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
