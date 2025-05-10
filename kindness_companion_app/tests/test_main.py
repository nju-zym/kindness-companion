import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from kindness_companion_app.frontend.main_window import MainWindow
from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.user_manager import UserManager
from kindness_companion_app.backend.challenge_manager import ChallengeManager
from kindness_companion_app.backend.progress_tracker import ProgressTracker
from kindness_companion_app.backend.reminder_scheduler import ReminderScheduler
from kindness_companion_app.backend.wall_manager import WallManager
from kindness_companion_app.main import main, load_fonts


class TestMainWindow(unittest.TestCase):
    """Test cases for the main window."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        # Create QApplication instance
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Set up test fixtures for each test method."""
        # Create mock managers
        self.mock_user_manager = MagicMock(spec=UserManager)
        self.mock_challenge_manager = MagicMock(spec=ChallengeManager)
        self.mock_progress_tracker = MagicMock(spec=ProgressTracker)
        self.mock_reminder_scheduler = MagicMock(spec=ReminderScheduler)
        self.mock_wall_manager = MagicMock(spec=WallManager)

        # Create the main window instance
        self.main_window = MainWindow(
            self.mock_user_manager,
            self.mock_challenge_manager,
            self.mock_progress_tracker,
            self.mock_reminder_scheduler,
            self.mock_wall_manager,
        )

    def test_initialization(self):
        """Test main window initialization."""
        # Verify that the window was initialized correctly
        self.assertIsNotNone(self.main_window)
        self.assertIsNotNone(self.main_window.logger)
        self.assertEqual(
            self.main_window.windowTitle(), "善行伴侣 (Kindness Companion)"
        )

    def test_window_size(self):
        """Test window size."""
        # Verify that the window size is set correctly
        self.assertGreater(self.main_window.width(), 0)
        self.assertGreater(self.main_window.height(), 0)
        self.assertGreaterEqual(self.main_window.minimumWidth(), 800)
        self.assertGreaterEqual(self.main_window.minimumHeight(), 600)

    def test_ui_components(self):
        """Test UI components initialization."""
        # Verify that all UI components are initialized
        self.assertIsNotNone(self.main_window.central_widget)
        self.assertIsNotNone(self.main_window.main_layout)
        self.assertIsNotNone(self.main_window.nav_widget)
        self.assertIsNotNone(self.main_window.nav_layout)
        self.assertIsNotNone(self.main_window.title_label)

    def test_navigation(self):
        """Test navigation functionality."""
        # Test showing different screens
        self.main_window.show_login()
        self.main_window.show_register()
        self.main_window.show_challenges()
        self.main_window.show_checkin()
        self.main_window.show_progress()
        self.main_window.show_reminders()
        self.main_window.show_community()
        self.main_window.show_profile()

    def test_theme_switching(self):
        """Test theme switching functionality."""
        # Test theme switching
        self.main_window.toggle_theme()
        self.assertIn(self.main_window.current_theme, ["light", "dark"])

    def test_reminder_handling(self):
        """Test reminder handling."""
        # Create a mock reminder
        mock_reminder = {
            "title": "Test Reminder",
            "message": "This is a test reminder",
            "time": "2024-03-20 10:00:00",
        }

        # Test showing reminder
        self.main_window.show_reminder(mock_reminder)

    def test_user_management(self):
        """Test user management functionality."""
        # Test login
        mock_user = {"id": 1, "username": "test_user"}
        self.main_window.on_login_successful(mock_user)

        # Test logout
        self.main_window.logout()

    def test_resize_handling(self):
        """Test window resize handling."""
        # Create a mock resize event
        mock_event = MagicMock()
        mock_event.size.return_value = QSize(1000, 800)

        # Test resize event handling
        self.main_window.resizeEvent(mock_event)


class TestMain(unittest.TestCase):
    """Test cases for the main application functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        # Create QApplication instance
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Set up test fixtures for each test method."""
        # Create mock managers
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_user_manager = MagicMock(spec=UserManager)
        self.mock_challenge_manager = MagicMock(spec=ChallengeManager)
        self.mock_progress_tracker = MagicMock(spec=ProgressTracker)
        self.mock_reminder_scheduler = MagicMock(spec=ReminderScheduler)
        self.mock_wall_manager = MagicMock(spec=WallManager)

    def test_load_fonts(self):
        """Test loading custom fonts."""
        # Test loading fonts
        loaded_fonts = load_fonts()

        # Verify that fonts were loaded
        self.assertIsInstance(loaded_fonts, list)
        self.assertTrue(len(loaded_fonts) > 0)

    @patch("kindness_companion_app.main.DatabaseManager")
    @patch("kindness_companion_app.main.UserManager")
    @patch("kindness_companion_app.main.ChallengeManager")
    @patch("kindness_companion_app.main.ProgressTracker")
    @patch("kindness_companion_app.main.ReminderScheduler")
    @patch("kindness_companion_app.main.WallManager")
    @patch("kindness_companion_app.main.MainWindow")
    def test_main_initialization(
        self,
        mock_window,
        mock_wall,
        mock_reminder,
        mock_progress,
        mock_challenge,
        mock_user,
        mock_db,
    ):
        """Test main application initialization."""
        # Configure mocks
        mock_db.return_value = self.mock_db_manager
        mock_user.return_value = self.mock_user_manager
        mock_challenge.return_value = self.mock_challenge_manager
        mock_progress.return_value = self.mock_progress_tracker
        mock_reminder.return_value = self.mock_reminder_scheduler
        mock_wall.return_value = self.mock_wall_manager
        mock_window.return_value = MagicMock(spec=MainWindow)

        # Run main function
        with patch("sys.exit") as mock_exit:
            main()

            # Verify that all managers were initialized
            mock_db.assert_called_once()
            mock_user.assert_called_once_with(self.mock_db_manager)
            mock_challenge.assert_called_once_with(self.mock_db_manager)
            mock_progress.assert_called_once_with(self.mock_db_manager)
            mock_reminder.assert_called_once_with(self.mock_db_manager)
            mock_wall.assert_called_once_with(self.mock_db_manager)

            # Verify that MainWindow was created with all managers
            mock_window.assert_called_once_with(
                user_manager=self.mock_user_manager,
                challenge_manager=self.mock_challenge_manager,
                progress_tracker=self.mock_progress_tracker,
                reminder_scheduler=self.mock_reminder_scheduler,
                wall_manager=self.mock_wall_manager,
            )

            # Verify that the window was shown
            mock_window.return_value.show.assert_called_once()

            # Verify that the application event loop was started
            self.assertTrue(hasattr(self.app, "exec"))

    def test_main_window_creation(self):
        """Test creating the main window with all required components."""
        # Create main window with mock managers
        window = MainWindow(
            user_manager=self.mock_user_manager,
            challenge_manager=self.mock_challenge_manager,
            progress_tracker=self.mock_progress_tracker,
            reminder_scheduler=self.mock_reminder_scheduler,
            wall_manager=self.mock_wall_manager,
        )

        # Verify window properties
        self.assertEqual(window.windowTitle(), "善行伴侣 (Kindness Companion)")
        self.assertIsNotNone(window.central_widget)
        self.assertIsNotNone(window.content_widget)
        self.assertIsNotNone(window.nav_layout)


if __name__ == "__main__":
    unittest.main()
