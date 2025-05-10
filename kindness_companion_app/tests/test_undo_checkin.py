import unittest
import datetime
from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.progress_tracker import ProgressTracker
from kindness_companion_app.backend.logger_config import progress_logger


class TestUndoCheckIn(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.db_manager = DatabaseManager(
            ":memory:"
        )  # Use in-memory database for testing

        # Create test user
        self.db_manager.execute_insert(
            """
            INSERT INTO users (id, username, password_hash, email)
            VALUES (?, ?, ?, ?)
            """,
            (1, "test_user", "test_hash", "test@example.com"),
        )

        # Create test challenge
        self.db_manager.execute_insert(
            """
            INSERT INTO challenges (id, title, description, category, difficulty)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "Test Challenge", "Test Description", "Test Category", 1),
        )

        # Subscribe user to challenge
        self.db_manager.execute_insert(
            """
            INSERT INTO user_challenges (user_id, challenge_id)
            VALUES (?, ?)
            """,
            (1, 1),
        )

        self.progress_tracker = ProgressTracker(self.db_manager)
        self.user_id = 1
        self.challenge_id = 1
        self.test_date = datetime.date.today().isoformat()

    def test_undo_check_in_success(self):
        """Test successful undo of a check-in."""
        # First create a check-in
        success = self.progress_tracker.check_in(
            self.user_id, self.challenge_id, self.test_date
        )
        self.assertTrue(success, "Check-in should be successful")

        # Verify check-in exists
        check_ins = self.progress_tracker.get_check_ins(
            self.user_id, self.challenge_id, self.test_date, self.test_date
        )
        self.assertEqual(len(check_ins), 1, "Should have one check-in")

        # Try to undo the check-in
        success = self.progress_tracker.undo_check_in(
            self.user_id, self.challenge_id, self.test_date
        )
        self.assertTrue(success, "Undo should be successful")

        # Verify check-in is gone
        check_ins = self.progress_tracker.get_check_ins(
            self.user_id, self.challenge_id, self.test_date, self.test_date
        )
        self.assertEqual(len(check_ins), 0, "Should have no check-ins after undo")

    def test_undo_nonexistent_check_in(self):
        """Test undoing a check-in that doesn't exist."""
        success = self.progress_tracker.undo_check_in(
            self.user_id, self.challenge_id, self.test_date
        )
        self.assertFalse(success, "Undo should fail for nonexistent check-in")

    def test_undo_check_in_invalid_date(self):
        """Test undoing a check-in with invalid date."""
        success = self.progress_tracker.undo_check_in(
            self.user_id, self.challenge_id, "invalid-date"
        )
        self.assertFalse(success, "Undo should fail for invalid date")

    def test_undo_check_in_no_date(self):
        """Test undoing a check-in with no date."""
        success = self.progress_tracker.undo_check_in(
            self.user_id, self.challenge_id, ""
        )
        self.assertFalse(success, "Undo should fail for no date")


if __name__ == "__main__":
    unittest.main()
