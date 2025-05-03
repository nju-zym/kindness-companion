import unittest
import os
import tempfile
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.user_manager import UserManager
from backend.database_manager import DatabaseManager

class TestUserManager(unittest.TestCase):
    """Test cases for the UserManager class."""

    def setUp(self):
        """Set up a mock database manager for testing."""
        # Create a mock DatabaseManager
        self.mock_db_manager = MagicMock(spec=DatabaseManager)

        # Create a UserManager instance with the mock database manager
        self.user_manager = UserManager(self.mock_db_manager)

        # Sample user data
        self.sample_user = {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "bio": "Test bio",
            "avatar_path": ":/images/profilePicture.png",
            "avatar": None,
            "registration_date": "2023-01-01 12:00:00",
            "ai_consent_given": None
        }

    def test_register_user(self):
        """Test registering a new user."""
        # Configure the mock to return None for the query (user doesn't exist)
        self.mock_db_manager.execute_query.return_value = None

        # Configure the mock to return a user ID for the insert
        self.mock_db_manager.execute_insert.return_value = 1

        # Configure the mock to return the new user for the query
        self.mock_db_manager.execute_query.side_effect = [
            None,  # First call (check if user exists)
            [{
                "id": 1,
                "username": "test_user",
                "email": "test@example.com",
                "bio": "",
                "avatar_path": ":/images/profilePicture.png",
                "avatar": None,
                "created_at": "2023-01-01 12:00:00"
            }]  # Second call (get the new user)
        ]

        # Register a new user
        result = self.user_manager.register_user("test_user", "password", "test@example.com")

        # Check that the result is the expected user
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["email"], "test@example.com")

        # Check that the mocks were called correctly
        self.mock_db_manager.execute_query.assert_called()
        self.mock_db_manager.execute_insert.assert_called_once()

    def test_login(self):
        """Test logging in a user."""
        # Configure the mock to return a user for the query
        self.mock_db_manager.execute_query.return_value = [{
            "id": 1,
            "username": "test_user",
            "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8:salt",  # sha256 hash of "password"
            "email": "test@example.com",
            "bio": "Test bio",
            "avatar_path": ":/images/profilePicture.png",
            "avatar": None,
            "created_at": "2023-01-01 12:00:00"
        }]

        # Mock the _hash_password method to return a known hash
        with patch.object(self.user_manager, '_hash_password', return_value=("5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", "salt")):
            # Log in the user
            result = self.user_manager.login("test_user", "password")

        # Check that the result is the expected user
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["email"], "test@example.com")

        # Check that the mocks were called correctly
        self.mock_db_manager.execute_query.assert_called_once()
        self.mock_db_manager.execute_update.assert_called_once()  # Update last login time

    def test_get_ai_consent_true(self):
        """Test getting AI consent when it's set to True."""
        # Configure the mock to return a user with AI consent set to 1 (True)
        self.mock_db_manager.execute_query.return_value = [{
            "ai_consent_given": 1
        }]

        # Get AI consent
        result = self.user_manager.get_ai_consent(1)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT ai_consent_given FROM users WHERE id = ?",
            (1,)
        )

    def test_get_ai_consent_false(self):
        """Test getting AI consent when it's set to False."""
        # Configure the mock to return a user with AI consent set to 0 (False)
        self.mock_db_manager.execute_query.return_value = [{
            "ai_consent_given": 0
        }]

        # Get AI consent
        result = self.user_manager.get_ai_consent(1)

        # Check that the result is False
        self.assertFalse(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT ai_consent_given FROM users WHERE id = ?",
            (1,)
        )

    def test_get_ai_consent_none(self):
        """Test getting AI consent when it's not set (None)."""
        # Configure the mock to return a user with AI consent set to None
        self.mock_db_manager.execute_query.return_value = [{
            "ai_consent_given": None
        }]

        # Get AI consent
        result = self.user_manager.get_ai_consent(1)

        # Check that the result is None
        self.assertIsNone(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT ai_consent_given FROM users WHERE id = ?",
            (1,)
        )

    def test_set_ai_consent_true(self):
        """Test setting AI consent to True."""
        # Configure the mock to return 1 affected row for the update
        self.mock_db_manager.execute_update.return_value = 1

        # Set AI consent to True
        result = self.user_manager.set_ai_consent(1, True)

        # Check that the result is True (success)
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "UPDATE users SET ai_consent_given = ? WHERE id = ?",
            (1, 1)  # 1 for True, 1 for user_id
        )

    def test_set_ai_consent_false(self):
        """Test setting AI consent to False."""
        # Configure the mock to return 1 affected row for the update
        self.mock_db_manager.execute_update.return_value = 1

        # Set AI consent to False
        result = self.user_manager.set_ai_consent(1, False)

        # Check that the result is True (success)
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "UPDATE users SET ai_consent_given = ? WHERE id = ?",
            (0, 1)  # 0 for False, 1 for user_id
        )

    def test_set_ai_consent_user_not_found(self):
        """Test setting AI consent when the user is not found."""
        # Configure the mock to return 0 affected rows for the update
        self.mock_db_manager.execute_update.return_value = 0

        # Set AI consent
        result = self.user_manager.set_ai_consent(999, True)

        # Check that the result is False (failure)
        self.assertFalse(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "UPDATE users SET ai_consent_given = ? WHERE id = ?",
            (1, 999)  # 1 for True, 999 for user_id
        )

    def test_update_profile_with_ai_consent(self):
        """Test updating user profile with AI consent."""
        # Configure the mock to return 1 affected row for the update
        self.mock_db_manager.execute_update.return_value = 1

        # Set the current user
        self.user_manager.current_user = self.sample_user.copy()

        # Update the profile with AI consent
        result = self.user_manager.set_ai_consent(1, True)

        # Check that the result is True (success)
        self.assertTrue(result)

        # Check that the current user was updated
        self.assertTrue(self.user_manager.current_user["ai_consent_given"])

if __name__ == '__main__':
    unittest.main()
