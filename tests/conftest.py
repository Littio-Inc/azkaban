"""Test configuration and utilities."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.user import Base


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = self.SessionLocal()

    def tearDown(self):
        """Clean up after tests."""
        self.db_session.close()
        Base.metadata.drop_all(self.engine)


def get_mock_current_user():
    """Get mock current user for testing."""
    return {
        "firebase_uid": "test-firebase-uid-123",
        "email": "test@littio.co",
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
    }


def get_mock_admin_user():
    """Get mock admin user for testing."""
    return {
        "firebase_uid": "admin-firebase-uid-123",
        "email": "admin@littio.co",
        "name": "Admin User",
        "picture": "https://example.com/admin.jpg",
        "role": "admin",
        "is_active": True,
    }


def get_sample_user_data():
    """Get sample user data for testing."""
    return {
        "firebase_uid": "test-firebase-uid-123",
        "email": "test@littio.co",
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
    }
