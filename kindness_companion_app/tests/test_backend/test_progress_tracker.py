import unittest
import os
import sys
from unittest.mock import MagicMock
import datetime

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.progress_tracker import ProgressTracker
from backend.database_manager import DatabaseManager

class TestProgressTracker(unittest.TestCase):
    """Test cases for the ProgressTracker class."""

    def setUp(self):
        """Set up a mock database manager for testing."""
        # Create a mock DatabaseManager
        self.mock_db_manager = MagicMock(spec=DatabaseManager)

        # Create a ProgressTracker instance with the mock database manager
        self.progress_tracker = ProgressTracker(self.mock_db_manager)

        # Sample progress data
        self.sample_progress = [
            {
                "id": 1,
                "user_id": 1,
                "challenge_id": 1,
                "check_in_date": "2023-01-01",
                "notes": "Helped an elderly person cross the street",
                "created_at": "2023-01-01 12:00:00"
            },
            {
                "id": 2,
                "user_id": 1,
                "challenge_id": 2,
                "check_in_date": "2023-01-02",
                "notes": "Volunteered at a local shelter",
                "created_at": "2023-01-02 12:00:00"
            },
            {
                "id": 3,
                "user_id": 1,
                "challenge_id": 1,
                "check_in_date": "2023-01-03",
                "notes": "Smiled at everyone I met today",
                "created_at": "2023-01-03 12:00:00"
            }
        ]

    def test_add_check_in(self):
        """Test adding a check-in."""
        # Configure the mock to return 1 for the insert
        self.mock_db_manager.execute_insert.return_value = 1

        # Add a check-in
        result = self.progress_tracker.add_check_in(1, 1, "2023-01-01", "Test notes")

        # Check that the result is 1 (the new ID)
        self.assertEqual(result, 1)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_insert.assert_called_once()

    def test_get_check_in(self):
        """Test getting a check-in by ID."""
        # Configure the mock to return a single check-in
        self.mock_db_manager.execute_query.return_value = [self.sample_progress[0]]

        # Get a check-in by ID
        result = self.progress_tracker.get_check_in(1)

        # Check that the result is the expected check-in
        self.assertEqual(result, self.sample_progress[0])

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM progress WHERE id = ?",
            (1,)
        )

    def test_get_check_in_not_found(self):
        """Test getting a check-in by ID when it doesn't exist."""
        # Configure the mock to return an empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get a check-in by ID
        result = self.progress_tracker.get_check_in(999)

        # Check that the result is None
        self.assertIsNone(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM progress WHERE id = ?",
            (999,)
        )

    def test_get_user_check_ins(self):
        """Test getting check-ins for a user."""
        # Configure the mock to return check-ins
        self.mock_db_manager.execute_query.return_value = self.sample_progress

        # Get user check-ins
        result = self.progress_tracker.get_user_check_ins(1, 1)

        # Check that the result is the expected check-ins
        self.assertEqual(result, self.sample_progress)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM progress WHERE user_id = ? AND challenge_id = ? ORDER BY check_in_date DESC",
            (1, 1)
        )

    def test_get_all_user_check_ins(self):
        """Test getting all check-ins for a user."""
        # Configure the mock to return check-ins
        self.mock_db_manager.execute_query.return_value = self.sample_progress

        # Get all user check-ins
        result = self.progress_tracker.get_all_user_check_ins(1)

        # Check that the result is the expected check-ins
        self.assertEqual(result, self.sample_progress)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM progress WHERE user_id = ? ORDER BY check_in_date DESC",
            (1,)
        )

    def test_get_all_user_check_ins_with_date_range(self):
        """Test getting all check-ins for a user within a date range."""
        # Configure the mock to return check-ins
        self.mock_db_manager.execute_query.return_value = self.sample_progress

        # Get all user check-ins within a date range
        result = self.progress_tracker.get_all_user_check_ins(1, "2023-01-01", "2023-01-03")

        # Check that the result is the expected check-ins
        self.assertEqual(result, self.sample_progress)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT * FROM progress WHERE user_id = ? AND check_in_date BETWEEN ? AND ? ORDER BY check_in_date DESC",
            (1, "2023-01-01", "2023-01-03")
        )

    def test_get_check_in_dates(self):
        """Test getting check-in dates for a user."""
        # Configure the mock to return dates
        self.mock_db_manager.execute_query.return_value = [
            {"check_in_date": "2023-01-01"},
            {"check_in_date": "2023-01-02"},
            {"check_in_date": "2023-01-03"}
        ]

        # Get check-in dates
        result = self.progress_tracker.get_check_in_dates(1)

        # Check that the result is the expected dates
        self.assertEqual(result, ["2023-01-01", "2023-01-02", "2023-01-03"])

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT DISTINCT check_in_date FROM progress WHERE user_id = ? ORDER BY check_in_date",
            (1,)
        )

    def test_get_total_check_ins(self):
        """Test getting the total number of check-ins for a user."""
        # Configure the mock to return a count
        self.mock_db_manager.execute_query.return_value = [{"count": 3}]

        # Get total check-ins
        result = self.progress_tracker.get_total_check_ins(1)

        # Check that the result is the expected count
        self.assertEqual(result, 3)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once_with(
            "SELECT COUNT(*) as count FROM progress WHERE user_id = ?",
            (1,)
        )

    def test_get_current_streak(self):
        """Test getting the current streak for a user and challenge."""
        # Today's date
        today = datetime.date.today()

        # Generate a sequence of consecutive dates ending with today
        dates = []
        for i in range(3):
            date = today - datetime.timedelta(days=i)
            dates.append({"check_in_date": date.isoformat()})

        # Configure the mock to return the dates in reverse order (most recent first)
        self.mock_db_manager.execute_query.return_value = list(reversed(dates))

        # Mock the get_streak method to return 3
        with unittest.mock.patch.object(self.progress_tracker, 'get_streak', return_value=3) as mock_get_streak:
            # Get current streak
            result = self.progress_tracker.get_current_streak(1, 1)

            # Check that the result is the expected streak
            self.assertEqual(result, 3)

            # Check that the mock was called correctly
            mock_get_streak.assert_called_once_with(1, 1)

    def test_get_longest_streak(self):
        """Test getting the longest streak for a user and challenge."""
        # Configure the mock to return check-ins with gaps
        self.mock_db_manager.execute_query.return_value = [
            {"check_in_date": "2022-12-28"},
            {"check_in_date": "2022-12-29"},
            {"check_in_date": "2022-12-30"},
            {"check_in_date": "2022-12-31"},
            {"check_in_date": "2023-01-01"},
            # Gap on 2023-01-02
            {"check_in_date": "2023-01-03"},
            {"check_in_date": "2023-01-04"},
            {"check_in_date": "2023-01-05"}
        ]

        # Get longest streak
        result = self.progress_tracker.get_longest_streak(1, 1)

        # Check that the result is the expected streak (5 days)
        # Note: The implementation counts consecutive days, so we expect 5 days
        # (2022-12-28 to 2023-01-01) as the longest streak
        self.assertEqual(result, 5)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_completion_rate(self):
        """Test getting the completion rate for a user and challenge."""
        # Mock the get_check_ins method to return sample check-ins
        with unittest.mock.patch.object(self.progress_tracker, 'get_check_ins') as mock_get_check_ins:
            # Return sample check-ins with check_in_date field
            mock_get_check_ins.return_value = [
                {"check_in_date": "2023-01-01"},
                {"check_in_date": "2023-01-02"},
                {"check_in_date": "2023-01-03"}
            ]

            # Mock datetime.date.today() to return a fixed date
            with unittest.mock.patch('datetime.date') as mock_date:
                mock_date.today.return_value = datetime.date(2023, 1, 10)
                mock_date.fromisoformat.side_effect = datetime.date.fromisoformat

                # Get completion rate (3 check-ins out of 30 days = 10%)
                result = self.progress_tracker.get_completion_rate(1, 1)

            # Check that the result is the expected rate (3 check-ins out of 30 days = 10%)
            self.assertAlmostEqual(result, 0.1)  # 10%

            # Check that the mock was called correctly
            mock_get_check_ins.assert_called_once()

if __name__ == '__main__':
    unittest.main()
