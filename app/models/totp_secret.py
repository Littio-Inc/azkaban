"""TOTP secret model for Google Authenticator."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TOTPSecret(Base):
    """TOTP secret for user two-factor authentication."""

    __tablename__ = "totp_secrets"

    id = Column(String, primary_key=True)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    secret = Column(String, nullable=False)  # Base32 encoded TOTP secret
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)  # When user verified the setup
