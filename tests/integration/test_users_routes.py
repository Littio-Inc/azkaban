"""Integration tests for user routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.admin import get_admin_user
from app.middleware.auth import get_current_user
from app.routes.users_routes import router


class TestUsersRoutes(unittest.TestCase):
    """Test cases for user routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.mock_current_user = {
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        self.mock_admin_user = {
            "id": "admin-1",
            "firebase_uid": "admin-uid-123",
            "email": "admin@littio.co",
            "name": "Admin User",
            "role": "admin",
            "is_active": True,
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clear dependency overrides after each test
        self.app.dependency_overrides.clear()

    @patch("app.routes.users_routes.UserService")
    def test_sync_user_new(
        self, mock_user_service
    ):
        """Test syncing a new user."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user
        mock_user_service.create_or_update_user.return_value = {
            "id": "user-1",
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "role": "user",
            "is_active": False,
        }

        response = self.client.post(
            "/sync",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["firebase_uid"], "test-uid-123")
        mock_user_service.create_or_update_user.assert_called_once()

    @patch("app.routes.users_routes.UserService")
    def test_get_current_user_info(
        self, mock_user_service
    ):
        """Test getting current user info."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user
        mock_user_service.get_user_by_firebase_uid.return_value = {
            "id": "user-1",
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "role": "user",
            "is_active": True,
        }

        response = self.client.get(
            "/me",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["firebase_uid"], "test-uid-123")
        self.assertIn("role", data)

    def test_get_current_user_info_no_db(self):
        """Test getting current user info when not in database."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        with patch("app.routes.users_routes.UserService") as mock_user_service:
            mock_user_service.get_user_by_firebase_uid.return_value = None
            response = self.client.get(
                "/me",
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["firebase_uid"], "test-uid-123")

    def test_get_current_user_info_no_firebase_uid(self):
        """Test getting current user info when no firebase_uid."""
        mock_user_no_uid = {
            "email": "test@littio.co",
            "name": "Test User",
        }
        self.app.dependency_overrides[get_current_user] = lambda: mock_user_no_uid

        response = self.client.get(
            "/me",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "test@littio.co")
        self.assertNotIn("firebase_uid", data)

    def test_get_my_permissions(self):
        """Test getting user permissions."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        response = self.client.get(
            "/me/permissions",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("permissions", data)

    @patch("app.routes.users_routes.UserService")
    def test_list_users(
        self, mock_user_service
    ):
        """Test listing users (admin only)."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user
        mock_user_service.get_all_users.return_value = [
            {
                "id": "user-1",
                "firebase_uid": "uid-1",
                "email": "user1@littio.co",
                "role": "user",
                "is_active": True,
            },
            {
                "id": "user-2",
                "firebase_uid": "uid-2",
                "email": "user2@littio.co",
                "role": "user",
                "is_active": False,
            },
        ]

        response = self.client.get(
            "",
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("users", data)
        self.assertEqual(len(data["users"]), 2)
        self.assertEqual(data["total"], 2)

    @patch("app.routes.users_routes.UserService")
    def test_update_user_status(
        self, mock_user_service
    ):
        """Test updating user status (admin only)."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user
        mock_user_service.update_user_status.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-1",
            "email": "user1@littio.co",
            "is_active": True,
        }

        response = self.client.patch(
            "/user-1/status",
            json={"is_active": True},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_active"])
        mock_user_service.update_user_status.assert_called_once_with("user-1", True)

    @patch("app.routes.users_routes.UserService")
    def test_update_user_status_not_found(
        self, mock_user_service
    ):
        """Test updating user status when user not found."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user
        mock_user_service.update_user_status.return_value = None

        response = self.client.patch(
            "/non-existent/status",
            json={"is_active": True},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuario no encontrado", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_admin_success(
        self, mock_user_service
    ):
        """Test updating user role as admin."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = self.mock_admin_user
        mock_user_service.get_user_by_id.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-1",
            "email": "user1@littio.co",
            "role": "user",
        }
        mock_user_service.update_user_role.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-1",
            "email": "user1@littio.co",
            "role": "admin",
        }

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "admin")

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_self_success(
        self, mock_user_service
    ):
        """Test updating own role as regular user."""
        mock_user = {
            "id": "user-1",
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "role": "user",
        }
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user
        mock_user_service.get_user_by_firebase_uid.return_value = mock_user
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_service.update_user_role.return_value = {
            "id": "user-1",
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "role": "admin",
        }

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "admin")

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_invalid_role(
        self, mock_user_service
    ):
        """Test updating user role with invalid role."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = self.mock_admin_user

        response = self.client.patch(
            "/user-1/role",
            json={"role": "invalid"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Rol inválido", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_no_firebase_uid(
        self, mock_user_service
    ):
        """Test updating user role without firebase_uid."""
        mock_user_no_uid = {
            "email": "test@littio.co",
            "name": "Test User",
        }
        self.app.dependency_overrides[get_current_user] = lambda: mock_user_no_uid

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Usuario no autenticado", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_user_not_found(
        self, mock_user_service
    ):
        """Test updating user role when user not found in database."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = None

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuario no encontrado en la base de datos", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_target_not_found(
        self, mock_user_service
    ):
        """Test updating user role when target user not found."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = self.mock_admin_user
        mock_user_service.get_user_by_id.return_value = None

        response = self.client.patch(
            "/non-existent/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuario objetivo no encontrado", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_forbidden(
        self, mock_user_service
    ):
        """Test updating user role when user tries to update another user's role."""
        mock_user = {
            "id": "user-1",
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "role": "user",
        }
        target_user = {
            "id": "user-2",
            "firebase_uid": "uid-2",
            "email": "user2@littio.co",
            "role": "user",
        }
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user
        mock_user_service.get_user_by_firebase_uid.return_value = mock_user
        mock_user_service.get_user_by_id.return_value = target_user

        response = self.client.patch(
            "/user-2/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("No tienes permisos", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_no_user_id(
        self, mock_user_service
    ):
        """Test updating user role when target user has no id."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = self.mock_admin_user
        mock_user_service.get_user_by_id.return_value = {
            "firebase_uid": "uid-1",
            "email": "user1@littio.co",
        }

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("ID de usuario no encontrado", response.json()["detail"])

    @patch("app.routes.users_routes.UserService")
    def test_update_user_role_update_returns_none(
        self, mock_user_service
    ):
        """Test updating user role when update_user_role returns None."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_admin_user
        mock_user_service.get_user_by_firebase_uid.return_value = self.mock_admin_user
        mock_user_service.get_user_by_id.return_value = {
            "id": "user-1",
            "firebase_uid": "uid-1",
            "email": "user1@littio.co",
        }
        mock_user_service.update_user_role.return_value = None

        response = self.client.patch(
            "/user-1/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuario no encontrado", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
