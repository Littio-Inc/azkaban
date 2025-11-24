"""Tests for user service."""

import unittest
from unittest.mock import MagicMock, patch

from faker import Faker
from sqlalchemy.exc import SQLAlchemyError

from app.common.enums import UserRole
from app.models.user import User
from app.user.service import UserService

fake = Faker()

# Constants
EMAIL_DOMAIN = "littio.co"
SESSION_LOCAL_PATH = "app.user.service.SessionLocal"
DB_ERROR_MESSAGE = "Database error"


def _get_test_email():
    """Get a test email address."""
    return fake.email(domain=EMAIL_DOMAIN)


def _create_db_error():
    """Create a database error for testing."""
    return SQLAlchemyError(DB_ERROR_MESSAGE)


class TestUserService(unittest.TestCase):
    """Test cases for UserService."""

    def setUp(self):
        """Set up test fixtures."""
        # No setup needed for these tests

    @patch(SESSION_LOCAL_PATH)
    def test_get_all_users_empty(self, mock_session_local):  # noqa: WPS210
        """Test getting all users when database is empty."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        all_mock = MagicMock()
        all_mock.return_value = []
        limit_mock.all = all_mock
        offset_mock.limit.return_value = limit_mock
        query_mock.offset.return_value = offset_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        users = UserService.get_all_users()
        self.assertEqual(users, [])
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_all_users_with_data(self, mock_session_local):
        """Test getting all users when database has data."""
        mock_user = self._create_mock_user()

        mock_db = MagicMock()
        query_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        all_mock = MagicMock()
        all_mock.return_value = [mock_user]
        limit_mock.all = all_mock
        offset_mock.limit.return_value = limit_mock
        query_mock.offset.return_value = offset_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        users = UserService.get_all_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["id"], mock_user.id)
        self.assertEqual(users[0]["email"], mock_user.email)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_found(self, mock_session_local):
        """Test getting user by Firebase UID when user exists."""
        firebase_uid = fake.uuid4()
        mock_user = self._create_mock_user(firebase_uid=firebase_uid)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_firebase_uid(firebase_uid)
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], mock_user.id)
        self.assertEqual(user["firebase_uid"], firebase_uid)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_not_found(self, mock_session_local):
        """Test getting user by Firebase UID when user does not exist."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_firebase_uid(fake.uuid4())
        self.assertIsNone(user)
        # close is called once in finally when no error occurs
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_email_found(self, mock_session_local):
        """Test getting user by email when user exists."""
        email_domain = "littio.co"
        email = fake.email(domain=email_domain)
        mock_user = self._create_mock_user(email=email)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], email)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_email_not_found(self, mock_session_local):
        """Test getting user by email when user does not exist."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_email(_get_test_email())
        self.assertIsNone(user)
        # close is called once in finally when no error occurs
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_is_admin_true(self, mock_session_local):
        """Test is_admin returns True for admin user."""
        mock_user = self._create_mock_user(role=UserRole.ADMIN.value)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = UserService.is_admin(mock_user.firebase_uid)
        self.assertTrue(result)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_is_admin_false(self, mock_session_local):
        """Test is_admin returns False for non-admin user."""
        mock_user = self._create_mock_user(role=UserRole.USER.value)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = UserService.is_admin(mock_user.firebase_uid)
        self.assertFalse(result)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_is_admin_user_not_found(self, mock_session_local):
        """Test is_admin returns False when user not found."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = UserService.is_admin(fake.uuid4())
        self.assertFalse(result)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_new_user(self, mock_session_local):
        """Test creating a new user."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        firebase_uid = fake.uuid4()
        email = _get_test_email()
        name = fake.name()

        with patch("app.user.service.User") as mock_user_class:
            mock_user = MagicMock()
            mock_user.id = fake.uuid4()
            mock_user.firebase_uid = firebase_uid
            mock_user.email = email
            mock_user.name = name
            mock_user.picture = None
            mock_user.role = UserRole.USER.value
            mock_user.is_active = False
            mock_user.created_at = None
            mock_user.updated_at = None
            mock_user.last_login = None
            mock_user_class.return_value = mock_user

            user = UserService.create_or_update_user(
                firebase_uid=firebase_uid,
                email=email,
                name=name
            )

            self.assertIsNotNone(user)
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_existing_user(self, mock_session_local):
        """Test updating an existing user."""
        firebase_uid = fake.uuid4()
        mock_user = self._create_mock_user(firebase_uid=firebase_uid)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        new_email = _get_test_email()
        new_name = fake.name()
        new_picture = fake.image_url()

        UserService.create_or_update_user(
            firebase_uid=firebase_uid,
            email=new_email,
            name=new_name,
            picture=new_picture
        )

        self.assertEqual(mock_user.email, new_email)
        self.assertEqual(mock_user.name, new_name)
        self.assertEqual(mock_user.picture, new_picture)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_success(self, mock_session_local):
        """Test updating user status successfully."""
        user_id = fake.uuid4()
        mock_user = self._create_mock_user(id=user_id, is_active=False)

        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.update_user_status(user_id, True)

        self.assertIsNotNone(user)
        self.assertTrue(mock_user.is_active)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        # close is called twice: once after getting user, once after commit
        self.assertEqual(mock_db.close.call_count, 2)

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_not_found(self, mock_session_local):
        """Test updating user status when user not found."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.update_user_status(fake.uuid4(), True)

        self.assertIsNone(user)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_all_users_query_error(self, mock_session_local):
        """Test get_all_users when query raises SQLAlchemyError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        users = UserService.get_all_users()
        self.assertEqual(users, [])
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_get_all_users_all_error(self, mock_session_local):
        """Test get_all_users when query.all() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        offset_mock = MagicMock()
        limit_mock = MagicMock()
        limit_mock.all.side_effect = _create_db_error()
        offset_mock.limit.return_value = limit_mock
        query_mock.offset.return_value = offset_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        users = UserService.get_all_users()
        self.assertEqual(users, [])
        # close is called twice: once in except, once in finally
        self.assertEqual(mock_db.close.call_count, 2)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_query_error(self, mock_session_local):
        """Test get_user_by_firebase_uid when query raises SQLAlchemyError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_firebase_uid(fake.uuid4())
        self.assertIsNone(user)
        # close is called at least once (in except, and finally may also execute)
        mock_db.close.assert_called()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_first_error(self, mock_session_local):
        """Test get_user_by_firebase_uid when query.first() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.side_effect = _create_db_error()
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_firebase_uid(fake.uuid4())
        self.assertIsNone(user)
        # close is called twice: once in except, once in finally
        self.assertEqual(mock_db.close.call_count, 2)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_email_query_error(self, mock_session_local):
        """Test get_user_by_email when query raises SQLAlchemyError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_email(_get_test_email())
        self.assertIsNone(user)
        # close is called at least once (in except, and finally may also execute)
        mock_db.close.assert_called()

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_email_first_error(self, mock_session_local):
        """Test get_user_by_email when query.first() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.side_effect = _create_db_error()
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService.get_user_by_email(_get_test_email())
        self.assertIsNone(user)
        # close is called twice: once in except, once in finally
        self.assertEqual(mock_db.close.call_count, 2)

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_query_error(self, mock_session_local):
        """Test create_or_update_user when query raises SQLAlchemyError in _get_user_by_firebase_uid_internal."""
        # When query fails in _get_user_by_firebase_uid_internal, it returns None
        # Then the code tries to create a new user, which should succeed
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.side_effect = _create_db_error()
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_session_local.return_value = mock_db

        with patch("app.user.service.User") as mock_user_class:
            mock_user = self._create_mock_user()
            mock_user_class.return_value = mock_user

            # Should create new user when _get_user_by_firebase_uid_internal returns None
            user = UserService.create_or_update_user(
                firebase_uid=fake.uuid4(),
                email=_get_test_email()
            )
            self.assertIsNotNone(user)
            mock_db.add.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_first_error(self, mock_session_local):
        """Test create_or_update_user when query.first() raises SQLAlchemyError."""
        # When query.first() fails in _get_user_by_firebase_uid_internal, it returns None
        # Then the code tries to create a new user
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.side_effect = _create_db_error()
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_session_local.return_value = mock_db

        with patch("app.user.service.User") as mock_user_class:
            mock_user = self._create_mock_user()
            mock_user_class.return_value = mock_user

            # Should create new user when _get_user_by_firebase_uid_internal returns None
            user = UserService.create_or_update_user(
                firebase_uid=fake.uuid4(),
                email=_get_test_email()
            )
            self.assertIsNotNone(user)
            mock_db.add.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_add_error(self, mock_session_local):
        """Test create_or_update_user when db.add() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = None
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.add.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        with self.assertRaises(SQLAlchemyError):
            UserService.create_or_update_user(
                firebase_uid=fake.uuid4(),
                email=_get_test_email()
            )
        mock_db.rollback.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_commit_error(self, mock_session_local):
        """Test create_or_update_user when db.commit() raises SQLAlchemyError."""
        mock_user = self._create_mock_user()
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.commit.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        with self.assertRaises(SQLAlchemyError):
            UserService.create_or_update_user(
                firebase_uid=mock_user.firebase_uid,
                email=_get_test_email()
            )
        mock_db.rollback.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_create_or_update_user_refresh_error(self, mock_session_local):
        """Test create_or_update_user when db.refresh() raises SQLAlchemyError."""
        mock_user = self._create_mock_user()
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.refresh.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        with self.assertRaises(SQLAlchemyError):
            UserService.create_or_update_user(
                firebase_uid=mock_user.firebase_uid,
                email=_get_test_email()
            )

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_query_error(self, mock_session_local):
        """Test update_user_status when query raises SQLAlchemyError in _get_user_by_id_internal."""
        # When query fails in _get_user_by_id_internal, it returns None
        # Then update_user_status returns None
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.side_effect = _create_db_error()
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        # _get_user_by_id_internal returns None on error, so update_user_status returns None
        user = UserService.update_user_status(fake.uuid4(), True)
        self.assertIsNone(user)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_first_error(self, mock_session_local):
        """Test update_user_status when query.first() raises SQLAlchemyError in _get_user_by_id_internal."""
        # When query.first() fails in _get_user_by_id_internal, it returns None
        # Then update_user_status returns None
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.side_effect = _create_db_error()
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        # _get_user_by_id_internal returns None on error, so update_user_status returns None
        user = UserService.update_user_status(fake.uuid4(), True)
        self.assertIsNone(user)
        mock_db.close.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_commit_error(self, mock_session_local):
        """Test update_user_status when db.commit() raises SQLAlchemyError."""
        user_id = fake.uuid4()
        mock_user = self._create_mock_user(id=user_id)
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.commit.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        with self.assertRaises(SQLAlchemyError):
            UserService.update_user_status(user_id, True)
        mock_db.rollback.assert_called_once()

    @patch(SESSION_LOCAL_PATH)
    def test_update_user_status_refresh_error(self, mock_session_local):
        """Test update_user_status when db.refresh() raises SQLAlchemyError."""
        user_id = fake.uuid4()
        mock_user = self._create_mock_user(id=user_id)
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        first_mock = MagicMock()
        first_mock.return_value = mock_user
        filter_mock.first = first_mock
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_db.refresh.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        with self.assertRaises(SQLAlchemyError):
            UserService.update_user_status(user_id, True)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_id_internal_query_error(self, mock_session_local):
        """Test _get_user_by_id_internal when query raises SQLAlchemyError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        user = UserService._get_user_by_id_internal(mock_db, fake.uuid4())
        self.assertIsNone(user)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_id_internal_first_error(self, mock_session_local):
        """Test _get_user_by_id_internal when query.first() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.side_effect = _create_db_error()
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService._get_user_by_id_internal(mock_db, fake.uuid4())
        self.assertIsNone(user)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_internal_query(self, mock_session_local):
        """Test _get_user_by_firebase_uid_internal when query raises SQLAlchemyError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = _create_db_error()
        mock_session_local.return_value = mock_db

        user = UserService._get_user_by_firebase_uid_internal(mock_db, fake.uuid4())
        self.assertIsNone(user)

    @patch(SESSION_LOCAL_PATH)
    def test_get_user_by_firebase_uid_internal_first(self, mock_session_local):
        """Test _get_user_by_firebase_uid_internal when query.first() raises SQLAlchemyError."""
        mock_db = MagicMock()
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.side_effect = _create_db_error()
        query_mock.filter.return_value = filter_mock
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        user = UserService._get_user_by_firebase_uid_internal(mock_db, fake.uuid4())
        self.assertIsNone(user)

    def _create_mock_user(self, **kwargs):  # noqa: WPS338
        """Create a mock user with faker data."""
        mock_user = MagicMock(spec=User)
        mock_user.id = kwargs.get("id", fake.uuid4())
        mock_user.firebase_uid = kwargs.get("firebase_uid", fake.uuid4())
        mock_user.email = kwargs.get("email", _get_test_email())
        mock_user.name = kwargs.get("name", fake.name())
        mock_user.picture = kwargs.get("picture", fake.image_url())
        mock_user.role = kwargs.get("role", UserRole.USER.value)
        mock_user.is_active = kwargs.get("is_active", False)
        mock_user.created_at = kwargs.get("created_at", None)
        mock_user.updated_at = kwargs.get("updated_at", None)
        mock_user.last_login = kwargs.get("last_login", None)
        return mock_user
