import unittest
import os
import sys
import sqlite3
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
            "ai_consent_given": True
        }
