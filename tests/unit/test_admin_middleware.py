"""Tests for admin middleware."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.middleware.admin import get_admin_user


class TestAdminMiddleware(unittest.TestCase):
    """Test cases for admin middleware."""

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_success(self, mock_user_service):
        """Test successful admin user authentication."""
        current_user = {
            "firebase_uid": "admin-uid-123",
            "email": "admin@littio.co",
            "name": "Admin User",
        }

        mock_user_service.is_admin.return_value = True
        mock_user_service.get_user_by_firebase_uid.return_value = {
            "id": "user-1",
            "firebase_uid": "admin-uid-123",
            "email": "admin@littio.co",
            "role": "admin",
            "is_active": True,
        }

        admin_user = get_admin_user(current_user)
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user["role"], "admin")
        mock_user_service.is_admin.assert_called_once_with("admin-uid-123")

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_not_admin(self, mock_user_service):
        """Test non-admin user trying to access admin endpoint."""
        current_user = {
            "firebase_uid": "user-uid-123",
            "email": "user@littio.co",
            "name": "Regular User",
        }

        mock_user_service.is_admin.return_value = False
        mock_user_service.get_user_by_email.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_admin_user(current_user)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("No tienes permisos de administrador", context.exception.detail)

    def test_get_admin_user_no_firebase_uid(self):
        """Test admin check without firebase_uid."""
        current_user = {
            "email": "user@littio.co",
            "name": "User",
        }

        with self.assertRaises(HTTPException) as context:
            get_admin_user(current_user)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Usuario no autenticado", context.exception.detail)

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_special_email_fallback(self, mock_user_service):
        """Test admin check with special email fallback."""
        current_user = {
            "firebase_uid": "uid-123",
            "email": "mauricio.quinche@littio.co",
            "name": "Mauricio",
        }

        mock_user_service.is_admin.return_value = False
        mock_user_service.get_user_by_email.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-123",
            "email": "mauricio.quinche@littio.co",
            "role": "admin",
            "is_active": True,
        }

        admin_user = get_admin_user(current_user)
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user["role"], "admin")
        mock_user_service.get_user_by_email.assert_called_once_with("mauricio.quinche@littio.co")

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_not_found_in_db(self, mock_user_service):
        """Test admin check when user not found in database."""
        current_user = {
            "firebase_uid": "admin-uid-123",
            "email": "admin@littio.co",
            "name": "Admin User",
        }

        mock_user_service.is_admin.return_value = True
        mock_user_service.get_user_by_firebase_uid.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_admin_user(current_user)
        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Usuario no encontrado en la base de datos", context.exception.detail)

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_special_email_not_found(self, mock_user_service):
        """Test admin check with special email but user not found."""
        current_user = {
            "firebase_uid": "uid-123",
            "email": "mauricio.quinche@littio.co",
            "name": "Mauricio",
        }

        mock_user_service.is_admin.return_value = False
        mock_user_service.get_user_by_email.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_admin_user(current_user)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("No tienes permisos de administrador", context.exception.detail)

    @patch("app.middleware.admin.UserService")
    def test_get_admin_user_special_email_not_admin(self, mock_user_service):
        """Test admin check with special email but user is not admin."""
        current_user = {
            "firebase_uid": "uid-123",
            "email": "mauricio.quinche@littio.co",
            "name": "Mauricio",
        }

        mock_user_service.is_admin.return_value = False
        mock_user_service.get_user_by_email.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-123",
            "email": "mauricio.quinche@littio.co",
            "role": "user",  # Not admin
            "is_active": True,
        }

        with self.assertRaises(HTTPException) as context:
            get_admin_user(current_user)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("No tienes permisos de administrador", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
