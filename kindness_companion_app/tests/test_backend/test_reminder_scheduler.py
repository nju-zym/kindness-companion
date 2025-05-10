import unittest
import os
import sys
from unittest.mock import MagicMock, patch
import datetime

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.reminder_scheduler import ReminderScheduler
from backend.database_manager import DatabaseManager

class TestReminderScheduler(unittest.TestCase):
    """Test cases for the ReminderScheduler class."""

    def setUp(self):
        """Set up a mock database manager for testing."""
        # Create a mock DatabaseManager
        self.mock_db_manager = MagicMock(spec=DatabaseManager)

        # Patch the APScheduler to avoid actually scheduling jobs
        self.scheduler_patcher = patch('backend.reminder_scheduler.BackgroundScheduler')
        self.mock_scheduler_class = self.scheduler_patcher.start()
        self.mock_scheduler = self.mock_scheduler_class.return_value

        # Create a ReminderScheduler instance with the mock database manager
        self.reminder_scheduler = ReminderScheduler(self.mock_db_manager)

        # Sample reminder data
        self.sample_reminders = [
            {
                "id": 1,
                "user_id": 1,
                "challenge_id": 1,
                "challenge_title": "每日微笑",
                "time": "08:00",
                "days": "0,1,2,3,4,5,6",
                "enabled": 1,
                "created_at": "2023-01-01 12:00:00"
            },
            {
                "id": 2,
                "user_id": 1,
                "challenge_id": 2,
                "challenge_title": "扶老助残",
                "time": "12:00",
                "days": "1,3,5",
                "enabled": 1,
                "created_at": "2023-01-01 12:00:00"
            }
        ]

    def tearDown(self):
        """Clean up after tests."""
        self.scheduler_patcher.stop()

    def test_create_reminder(self):
        """Test creating a reminder."""
        # Configure the mock to return a new reminder ID
        self.mock_db_manager.execute_insert.return_value = 3

        # Create a reminder
        result = self.reminder_scheduler.create_reminder(
            user_id=1,
            challenge_id=1,
            time="09:00",
            days_of_week=[0, 2, 4]  # Monday, Wednesday, Friday
        )

        # Check that the result is the new reminder ID
        self.assertEqual(result, 3)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_insert.assert_called_once()

        # Check that the scheduler was used to add a job
        self.mock_scheduler.add_job.assert_called_once()

    def test_update_reminder(self):
        """Test updating a reminder."""
        # Configure the mock to return 1 row affected
        self.mock_db_manager.execute_update.return_value = 1

        # Configure the mock to return the reminder for get_reminder
        self.mock_db_manager.execute_query.return_value = [self.sample_reminders[0]]

        # Configure the mock to have a job ID for the reminder
        self.reminder_scheduler.jobs[1] = "job1"

        # Update a reminder
        result = self.reminder_scheduler.update_reminder(
            reminder_id=1,
            time="10:00",
            days_of_week=[1, 3, 5]  # Tuesday, Thursday, Saturday
        )

        # Check that the result is True (successful)
        self.assertTrue(result)

        # Check that the mocks were called correctly
        self.mock_db_manager.execute_update.assert_called_once()

        # Check that the scheduler was used to remove and add a job
        self.mock_scheduler.remove_job.assert_called_once()
        self.mock_scheduler.add_job.assert_called_once()

    def test_delete_reminder(self):
        """Test deleting a reminder."""
        # Configure the mock to return 1 row affected
        self.mock_db_manager.execute_update.return_value = 1

        # Configure the mock to have a job ID for the reminder
        self.reminder_scheduler.jobs[1] = "job1"

        # Delete a reminder
        result = self.reminder_scheduler.delete_reminder(1)

        # Check that the result is True (successful)
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "DELETE FROM reminders WHERE id = ?",
            (1,)
        )

        # Check that the scheduler was used to remove a job
        self.mock_scheduler.remove_job.assert_called_once()

    def test_enable_reminder(self):
        """Test enabling a reminder."""
        # Configure the mock to return 1 row affected
        self.mock_db_manager.execute_update.return_value = 1

        # Configure the mock to return the reminder for get_reminder
        self.mock_db_manager.execute_query.return_value = [self.sample_reminders[0]]

        # Enable a reminder
        result = self.reminder_scheduler.enable_reminder(1)

        # Check that the result is True (successful)
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "UPDATE reminders SET enabled = 1 WHERE id = ?",
            (1,)
        )

        # Check that the scheduler was used to add a job
        self.mock_scheduler.add_job.assert_called_once()

    def test_disable_reminder(self):
        """Test disabling a reminder."""
        # Configure the mock to return 1 row affected
        self.mock_db_manager.execute_update.return_value = 1

        # Configure the mock to have a job ID for the reminder
        self.reminder_scheduler.jobs[1] = "job1"

        # Disable a reminder
        result = self.reminder_scheduler.disable_reminder(1)

        # Check that the result is True (successful)
        self.assertTrue(result)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_update.assert_called_once_with(
            "UPDATE reminders SET enabled = 0 WHERE id = ?",
            (1,)
        )

        # Check that the scheduler was used to remove a job
        self.mock_scheduler.remove_job.assert_called_once()

    def test_get_user_reminders(self):
        """Test getting reminders for a user."""
        # Configure the mock to return sample reminders
        self.mock_db_manager.execute_query.return_value = self.sample_reminders

        # Get user reminders
        result = self.reminder_scheduler.get_user_reminders(1)

        # Check that the result is the expected reminders
        self.assertEqual(result, self.sample_reminders)

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once()

    def test_load_all_reminders(self):
        """Test loading all reminders."""
        # Configure the mock to return sample reminders
        self.mock_db_manager.execute_query.return_value = self.sample_reminders

        # Load all reminders
        self.reminder_scheduler.load_all_reminders()

        # Check that the mock was called correctly
        self.mock_db_manager.execute_query.assert_called_once()

        # Check that the scheduler was used to add jobs (one for each reminder)
        self.assertEqual(self.mock_scheduler.add_job.call_count, len(self.sample_reminders))

    def test_shutdown(self):
        """Test shutting down the scheduler."""
        # Shutdown the scheduler
        self.reminder_scheduler.shutdown()

        # Check that the scheduler was shut down
        self.mock_scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
