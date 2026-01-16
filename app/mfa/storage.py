"""Storage for TOTP secrets using database."""

from datetime import datetime
import logging
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.totp_secret import TOTPSecret
from app.user.service import SessionLocal

logger = logging.getLogger(__name__)


def _store_secret_in_db(db: Session, firebase_uid: str, secret: str) -> None:
    """Store or update TOTP secret in database.

    Args:
        db: Database session
        firebase_uid: Firebase user ID
        secret: TOTP secret (base32)
    """
    existing = db.query(TOTPSecret).filter(
        TOTPSecret.firebase_uid == firebase_uid
    ).first()

    if existing:
        existing.secret = secret
        existing.is_active = True
        existing.verified_at = None
        existing.updated_at = datetime.utcnow()
    else:
        totp_secret = TOTPSecret(
            id=str(uuid.uuid4()),
            firebase_uid=firebase_uid,
            secret=secret,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(totp_secret)


def _store_secret_with_commit(db: Session, firebase_uid: str, secret: str) -> None:
    """Store secret and commit transaction.

    Args:
        db: Database session
        firebase_uid: Firebase user ID
        secret: TOTP secret (base32)
    """
    _store_secret_in_db(db, firebase_uid, secret)
    db.commit()
    logger.debug(f"Stored secret for user {firebase_uid}")


def _get_active_secret(db: Session, firebase_uid: str) -> TOTPSecret | None:
    """Get active TOTP secret from database.

    Args:
        db: Database session
        firebase_uid: Firebase user ID

    Returns:
        TOTPSecret or None if not found
    """
    return db.query(TOTPSecret).filter(
        TOTPSecret.firebase_uid == firebase_uid,
        TOTPSecret.is_active.is_(True),
    ).first()


def _get_secret_string(db: Session, firebase_uid: str) -> str | None:
    """Get TOTP secret string for user.

    Args:
        db: Database session
        firebase_uid: Firebase user ID

    Returns:
        str: TOTP secret or None if not found
    """
    totp_secret = _get_active_secret(db, firebase_uid)
    return totp_secret.secret if totp_secret else None


def _check_verification_status(db: Session, firebase_uid: str) -> bool:
    """Check if TOTP is verified for user.

    Args:
        db: Database session
        firebase_uid: Firebase user ID

    Returns:
        bool: True if verified, False otherwise
    """
    totp_secret = _get_active_secret(db, firebase_uid)
    return totp_secret.verified_at is not None if totp_secret else False


def _mark_verified_with_commit(db: Session, firebase_uid: str) -> None:
    """Mark TOTP as verified and commit.

    Args:
        db: Database session
        firebase_uid: Firebase user ID
    """
    totp_secret = _get_secret_by_uid(db, firebase_uid)
    if totp_secret:
        _mark_verified_in_db(totp_secret)
        db.commit()
        logger.debug(f"Marked as verified for user {firebase_uid}")


def _deactivate_with_commit(db: Session, firebase_uid: str) -> None:
    """Deactivate TOTP and commit.

    Args:
        db: Database session
        firebase_uid: Firebase user ID
    """
    totp_secret = _get_secret_by_uid(db, firebase_uid)
    if totp_secret:
        _deactivate_in_db(totp_secret)
        db.commit()
        logger.debug(f"Deactivated for user {firebase_uid}")


def _get_secret_by_uid(db: Session, firebase_uid: str) -> TOTPSecret | None:
    """Get TOTP secret by firebase_uid (any status).

    Args:
        db: Database session
        firebase_uid: Firebase user ID

    Returns:
        TOTPSecret or None if not found
    """
    return db.query(TOTPSecret).filter(
        TOTPSecret.firebase_uid == firebase_uid
    ).first()


def _mark_verified_in_db(totp_secret: TOTPSecret) -> None:
    """Mark TOTP secret as verified in database.

    Args:
        totp_secret: TOTP secret object
    """
    totp_secret.verified_at = datetime.utcnow()
    totp_secret.updated_at = datetime.utcnow()


def _deactivate_in_db(totp_secret: TOTPSecret) -> None:
    """Deactivate TOTP secret in database.

    Args:
        totp_secret: TOTP secret object
    """
    totp_secret.is_active = False
    totp_secret.updated_at = datetime.utcnow()


class TOTPStorage:
    """Storage for TOTP secrets using database."""

    @classmethod
    def store_secret(
        cls,
        firebase_uid: str,
        secret: str,
    ) -> None:
        """Store TOTP secret for user.

        Args:
            firebase_uid: Firebase user ID
            secret: TOTP secret (base32)
        """
        with SessionLocal() as db:
            try:
                _store_secret_with_commit(db, firebase_uid, secret)
            except SQLAlchemyError as db_error:
                db.rollback()
                logger.exception(f"Error storing TOTP secret: {db_error}")
                raise

    @classmethod
    def get_secret(cls, firebase_uid: str) -> str | None:
        """Get TOTP secret for user.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            str: TOTP secret or None if not found
        """
        with SessionLocal() as db:
            try:
                return _get_secret_string(db, firebase_uid)
            except SQLAlchemyError as db_error:
                logger.exception(f"Error getting TOTP secret: {db_error}")
                return None

    @classmethod
    def is_verified(cls, firebase_uid: str) -> bool:
        """Check if TOTP is verified for user.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            bool: True if verified, False otherwise
        """
        with SessionLocal() as db:
            try:
                return _check_verification_status(db, firebase_uid)
            except SQLAlchemyError as db_error:
                logger.exception(f"Error checking TOTP verification status: {db_error}")
                return False

    @classmethod
    def mark_verified(cls, firebase_uid: str) -> None:
        """Mark TOTP as verified for user.

        Args:
            firebase_uid: Firebase user ID
        """
        with SessionLocal() as db:
            try:
                _mark_verified_with_commit(db, firebase_uid)
            except SQLAlchemyError as db_error:
                db.rollback()
                logger.exception(f"Error marking TOTP as verified: {db_error}")
                raise

    @classmethod
    def deactivate(cls, firebase_uid: str) -> None:
        """Deactivate TOTP for user.

        Args:
            firebase_uid: Firebase user ID
        """
        with SessionLocal() as db:
            try:
                _deactivate_with_commit(db, firebase_uid)
            except SQLAlchemyError as db_error:
                db.rollback()
                logger.exception(f"Error deactivating TOTP: {db_error}")
                raise
