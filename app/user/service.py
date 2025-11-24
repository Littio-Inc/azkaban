"""User service for managing users in the database."""

from datetime import datetime
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.common.enums import UserRole
from app.common.secrets import get_secret
from app.models.user import Base, User

logger = logging.getLogger(__name__)

# Constants for error messages
ERROR_QUERYING_USER = "Error querying user: %s"
SPECIAL_ADMIN_EMAIL = "mauricio.quinche@littio.co"

# Initialize database tables on import
try:
    db_url = get_secret("DATABASE_URL") or "postgresql://azkaban:azkaban_dev@localhost:5432/azkaban_db"
except Exception as secret_error:
    logger.warning("Could not get database URL: %s", secret_error)
    db_url = "postgresql://azkaban:azkaban_dev@localhost:5432/azkaban_db"

try:
    engine_init = create_engine(db_url, pool_pre_ping=True)
except Exception as engine_error:
    logger.warning("Could not create engine: %s", engine_error)
    engine_init = None

if engine_init:
    try:
        Base.metadata.create_all(bind=engine_init)
    except Exception as create_error:
        logger.warning("Could not initialize database tables: %s", create_error)


# Database connection
DATABASE_URL = get_secret("DATABASE_URL") or "postgresql://azkaban:azkaban_dev@localhost:5432/azkaban_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def _user_to_dict(user: User) -> dict:
    """Convert User model to dictionary.

    Args:
        user: User model instance

    Returns:
        User dictionary
    """
    return {
        "id": user.id,
        "firebase_uid": user.firebase_uid,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


class UserService:  # noqa: WPS214
    """Service for user management operations."""

    @staticmethod
    def get_all_users(skip: int = 0, limit: int = 100) -> list[dict]:
        """Get all users from database.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user dictionaries
        """
        db = SessionLocal()
        try:
            query = db.query(User).offset(skip).limit(limit)
        except SQLAlchemyError as db_error:
            logger.error("Error querying users: %s", db_error)
            db.close()
            return []
        try:
            users = query.all()
        except SQLAlchemyError as db_error:
            logger.error("Error getting users: %s", db_error)
            db.close()
            return []
        finally:
            db.close()

        return [_user_to_dict(user) for user in users]

    @staticmethod
    def get_user_by_firebase_uid(firebase_uid: str) -> dict | None:
        """Get user by Firebase UID.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            User dictionary or None
        """
        db = SessionLocal()
        try:
            query = db.query(User).filter(User.firebase_uid == firebase_uid)
        except SQLAlchemyError as db_error:
            logger.error(ERROR_QUERYING_USER, db_error)
            db.close()
            return None
        try:
            user = query.first()
        except SQLAlchemyError as db_error:
            logger.error("Error getting user: %s", db_error)
            db.close()
            return None
        finally:
            db.close()

        if not user:
            return None
        return _user_to_dict(user)

    @staticmethod
    def get_user_by_email(email: str) -> dict | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User dictionary or None
        """
        db = SessionLocal()
        try:
            query = db.query(User).filter(User.email == email)
        except SQLAlchemyError as db_error:
            logger.error("Error querying user by email: %s", db_error)
            db.close()
            return None
        try:
            user = query.first()
        except SQLAlchemyError as db_error:
            logger.error("Error getting user by email: %s", db_error)
            db.close()
            return None
        finally:
            db.close()

        if not user:
            return None
        return _user_to_dict(user)

    @staticmethod
    def is_admin(firebase_uid: str) -> bool:
        """Check if user is admin.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            True if user is admin, False otherwise
        """
        db = SessionLocal()
        try:  # noqa: WPS229
            user = UserService._get_user_by_firebase_uid_internal(db, firebase_uid)
            if user is None:
                logger.debug("User not found in database")
                return False
            is_admin_result = user.role == UserRole.ADMIN.value
            logger.debug("User role: %s, is_admin: %s", user.role, is_admin_result)
            return is_admin_result
        finally:
            db.close()

    @staticmethod
    def create_or_update_user(
        firebase_uid: str,
        email: str,
        name: str | None = None,
        picture: str | None = None
    ) -> dict:
        """Create or update user in database.

        Args:
            firebase_uid: Firebase user ID
            email: User email
            name: User name
            picture: User profile picture URL

        Returns:
            User dictionary
        """
        db = SessionLocal()
        try:  # noqa: WPS229
            user = UserService._get_user_by_firebase_uid_internal(db, firebase_uid)
            if user:
                UserService._update_existing_user(user, email, name, picture)
            else:
                user = UserService._create_new_user(db, firebase_uid, email, name, picture)
            UserService._commit_and_refresh_user(db, user)
        finally:
            db.close()

        return _user_to_dict(user)

    @staticmethod
    def update_user_status(user_id: str, is_active: bool) -> dict | None:
        """Update user active status.

        Args:
            user_id: User ID
            is_active: New active status

        Returns:
            Updated user dictionary or None
        """
        db = SessionLocal()
        try:
            user = UserService._get_user_by_id_internal(db, user_id)
        finally:
            db.close()

        if user is None:
            return None

        user.is_active = is_active
        user.updated_at = datetime.utcnow()

        db = SessionLocal()
        try:
            UserService._commit_and_refresh_user(db, user)
        finally:
            db.close()

        return _user_to_dict(user)

    @staticmethod
    def _get_user_by_firebase_uid_internal(db: Session, firebase_uid: str) -> User | None:
        """Get user by Firebase UID from session.

        Args:
            db: Database session
            firebase_uid: Firebase user ID

        Returns:
            User instance or None
        """
        try:
            query = db.query(User).filter(User.firebase_uid == firebase_uid)
        except SQLAlchemyError as db_error:
            logger.error(ERROR_QUERYING_USER, db_error)
            return None
        try:
            return query.first()
        except SQLAlchemyError as db_error:
            logger.error("Error getting user: %s", db_error)
            return None

    @staticmethod
    def _update_existing_user(user: User, email: str, name: str | None, picture: str | None) -> None:
        """Update existing user fields.

        Args:
            user: User instance to update
            email: New email
            name: New name
            picture: New picture
        """
        user.email = email
        if name:
            user.name = name
        if picture:
            user.picture = picture
        user.updated_at = datetime.utcnow()

    @staticmethod
    def _create_new_user(
        db: Session,
        firebase_uid: str,
        email: str,
        name: str | None,
        picture: str | None
    ) -> User:
        """Create new user in database.

        Args:
            db: Database session
            firebase_uid: Firebase user ID
            email: User email
            name: User name
            picture: User profile picture URL

        Returns:
            Created User instance
        """
        is_admin_email = email == SPECIAL_ADMIN_EMAIL
        new_user = User(
            id=str(uuid.uuid4()),
            firebase_uid=firebase_uid,
            email=email,
            name=name,
            picture=picture,
            role=UserRole.ADMIN.value if is_admin_email else UserRole.USER.value,
            is_active=True if is_admin_email else False,
        )
        try:
            db.add(new_user)
        except SQLAlchemyError as db_error:
            logger.error("Error adding user: %s", db_error)
            db.rollback()
            raise
        return new_user

    @staticmethod
    def _commit_and_refresh_user(db: Session, user: User) -> None:
        """Commit and refresh user in database.

        Args:
            db: Database session
            user: User instance to commit
        """
        try:
            db.commit()
        except SQLAlchemyError as db_error:
            logger.error("Error committing user: %s", db_error)
            db.rollback()
            raise
        try:
            db.refresh(user)
        except SQLAlchemyError as db_error:
            logger.error("Error refreshing user: %s", db_error)
            raise

    @staticmethod
    def _get_user_by_id_internal(db: Session, user_id: str) -> User | None:
        """Get user by ID from session.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User instance or None
        """
        try:
            query = db.query(User).filter(User.id == user_id)
        except SQLAlchemyError as db_error:
            logger.error(ERROR_QUERYING_USER, db_error)
            return None
        try:
            return query.first()
        except SQLAlchemyError as db_error:
            logger.error("Error getting user: %s", db_error)
            return None
