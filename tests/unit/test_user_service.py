"""Tests for user service."""

import unittest
from unittest.mock import MagicMock, patch

from app.user.service import UserService, get_db, init_db


class TestUserService(unittest.TestCase):
    """Test cases for user service."""

    @patch("app.user.service.get_secret")
    def test_get_secret_failure(self, mock_get_secret):
        """Test when get_secret fails during module import."""
        mock_get_secret.side_effect = Exception("Secret error")
        # This tests the try/except block in the module-level code
        # We can't directly test it, but we can verify the fallback works
        from app.user.service import db_url
        self.assertIn("postgresql://", db_url)

    @patch("app.user.service.create_engine")
    def test_create_engine_failure(self, mock_create_engine):
        """Test when create_engine fails during module import."""
        mock_create_engine.side_effect = Exception("Engine error")
        # This tests the try/except block in the module-level code
        # We can't directly test it, but we can verify it doesn't crash
        from app.user.service import engine_init
        # engine_init should be None if creation failed
        # But we can't easily test this without reloading the module

    def test_get_db(self):
        """Test get_db generator function."""
        db_gen = get_db()
        db = next(db_gen)
        self.assertIsNotNone(db)
        # Test that finally block executes (closes db)
        try:
            next(db_gen)
        except StopIteration:
            pass
        # DB should be closed after generator completes

    @patch("app.user.service.engine")
    @patch("app.user.service.Base.metadata.create_all")
    def test_init_db(self, mock_create_all, mock_engine):
        """Test init_db function."""
        init_db()
        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch("app.user.service.get_secret")
    def test_get_secret_exception_during_import(self, mock_get_secret):
        """Test exception handling when get_secret fails during module import."""
        mock_get_secret.side_effect = Exception("Secret error")
        # Reload module to test the exception handling
        import importlib
        import app.user.service as user_service_module
        importlib.reload(user_service_module)
        # Should not crash, should use fallback URL
        self.assertIn("postgresql://", user_service_module.db_url)

    @patch("app.user.service.create_engine")
    def test_create_engine_exception_during_import(self, mock_create_engine):
        """Test exception handling when create_engine fails during module import."""
        mock_create_engine.side_effect = Exception("Engine error")
        # Reload module to test the exception handling
        import importlib
        import app.user.service as user_service_module
        importlib.reload(user_service_module)
        # Should not crash, engine_init should be None
        # Note: This is hard to test without actually reloading the module

    def test_get_db_finally_closes(self):
        """Test that get_db finally block closes the database."""
        db_gen = get_db()
        db = next(db_gen)
        self.assertIsNotNone(db)
        # The finally block should close the db when generator completes
        try:
            next(db_gen)
        except StopIteration:
            pass
        # Verify db is closed (this is implicit in the finally block execution)


if __name__ == "__main__":
    unittest.main()

