import unittest
import os
import sys
from unittest.mock import MagicMock

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.challenge_manager import ChallengeManager
from backend.database_manager import DatabaseManager

class TestChallengeManager(unittest.TestCase):
    """Test cases for the ChallengeManager class."""

    def setUp(self):
        """Set up a mock database manager for testing."""
        # Create a mock DatabaseManager
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        
        # Create a ChallengeManager instance with the mock database manager
        self.challenge_manager = ChallengeManager(self.mock_db_manager)
        
        # Sample challenge data
        self.sample_challenges = [
            {
                "id": 1,
                "title": "每日微笑",
                "description": "对遇到的每个人微笑，传递善意",
                "category": "日常行为",
                "difficulty": 1,
                "created_at": "2023-01-01 12:00:00"
            },
            {
                "id": 2,
                "title": "扶老助残",
                "description": "帮助老人或残障人士完成一项任务",
                "category": "社区服务",
                "difficulty": 2,
                "created_at": "2023-01-01 12:00:00"
            }
        ]
        
        # Sample user challenge data
        self.sample_user_challenges = [
            {
                "id": 1,
                "user_id": 1,
                "challenge_id": 1,
                "subscribed_at": "2023-01-01 12:00:00"
            },
            {
                "id": 2,
                "user_id": 1,
                "challenge_id": 2,
                "subscribed_at": "2023-01-01 12:00:00"
            }
        ]
    
    def test_get_all_challenges(self):
        """Test getting all challenges."""
        # Configure the mock to return sample challenges
        self.mock_db_manager.execute_query.return_value = self.sample_challenges
        
        # Get all challenges
        result = self.challenge_manager.get_all_challenges()
        
        # Check that the result is the expected challenges
        self.assertEqual(result, self.sample_challenges)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM challenges ORDER BY difficulty ASC, title ASC"
        )
    
    def test_get_challenge_by_id(self):
        """Test getting a challenge by ID."""
        # Configure the mock to return a single challenge
        self.mock_db_manager.execute_query.return_value = [self.sample_challenges[0]]
        
        # Get a challenge by ID
        result = self.challenge_manager.get_challenge_by_id(1)
        
        # Check that the result is the expected challenge
        self.assertEqual(result, self.sample_challenges[0])
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM challenges WHERE id = ?",
            (1,)
        )
    
    def test_get_challenge_by_id_not_found(self):
        """Test getting a challenge by ID when it doesn't exist."""
        # Configure the mock to return an empty list
        self.mock_db_manager.execute_query.return_value = []
        
        # Get a challenge by ID
        result = self.challenge_manager.get_challenge_by_id(999)
        
        # Check that the result is None
        self.assertIsNone(result)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM challenges WHERE id = ?",
            (999,)
        )
    
    def test_get_challenges_by_category(self):
        """Test getting challenges by category."""
        # Configure the mock to return challenges in a category
        self.mock_db_manager.execute_query.return_value = [self.sample_challenges[0]]
        
        # Get challenges by category
        result = self.challenge_manager.get_challenges_by_category("日常行为")
        
        # Check that the result is the expected challenges
        self.assertEqual(result, [self.sample_challenges[0]])
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM challenges WHERE category = ? ORDER BY difficulty ASC, title ASC",
            ("日常行为",)
        )
    
    def test_get_user_challenges(self):
        """Test getting challenges subscribed by a user."""
        # Configure the mock to return user challenges
        self.mock_db_manager.execute_query.return_value = self.sample_challenges
        
        # Get user challenges
        result = self.challenge_manager.get_user_challenges(1)
        
        # Check that the result is the expected challenges
        self.assertEqual(result, self.sample_challenges)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT c.* FROM challenges c "
            "JOIN user_challenges uc ON c.id = uc.challenge_id "
            "WHERE uc.user_id = ? "
            "ORDER BY c.difficulty ASC, c.title ASC",
            (1,)
        )
    
    def test_subscribe_to_challenge(self):
        """Test subscribing to a challenge."""
        # Configure the mock to return 1 for the insert
        self.mock_db_manager.execute_insert.return_value = 1
        
        # Subscribe to a challenge
        result = self.challenge_manager.subscribe_to_challenge(1, 1)
        
        # Check that the result is True (success)
        self.assertTrue(result)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_insert.assert_called_once_with(
            "INSERT OR IGNORE INTO user_challenges (user_id, challenge_id) VALUES (?, ?)",
            (1, 1)
        )
    
    def test_unsubscribe_from_challenge(self):
        """Test unsubscribing from a challenge."""
        # Configure the mock to return 1 for the update
        self.mock_db_manager.execute_update.return_value = 1
        
        # Unsubscribe from a challenge
        result = self.challenge_manager.unsubscribe_from_challenge(1, 1)
        
        # Check that the result is True (success)
        self.assertTrue(result)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "DELETE FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (1, 1)
        )
    
    def test_is_subscribed(self):
        """Test checking if a user is subscribed to a challenge."""
        # Configure the mock to return a subscription
        self.mock_db_manager.execute_query.return_value = [self.sample_user_challenges[0]]
        
        # Check if subscribed
        result = self.challenge_manager.is_subscribed(1, 1)
        
        # Check that the result is True
        self.assertTrue(result)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (1, 1)
        )
    
    def test_is_not_subscribed(self):
        """Test checking if a user is not subscribed to a challenge."""
        # Configure the mock to return an empty list
        self.mock_db_manager.execute_query.return_value = []
        
        # Check if subscribed
        result = self.challenge_manager.is_subscribed(1, 999)
        
        # Check that the result is False
        self.assertFalse(result)
        
        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (1, 999)
        )

if __name__ == '__main__':
    unittest.main()
