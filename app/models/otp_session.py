"""OTP session model for database storage."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OTPSession(Base):
    """OTP session model."""

    __tablename__ = "otp_sessions"

    id = Column(String, primary_key=True)
    firebase_uid = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
