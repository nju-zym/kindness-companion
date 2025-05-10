import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])

from frontend.profile_ui import ProfileWidget
from backend.user_manager import UserManager
from backend.progress_tracker import ProgressTracker
from backend.challenge_manager import ChallengeManager


class TestProfileUI(unittest.TestCase):
    """Test cases for the ProfileWidget class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock managers
        self.mock_user_manager = MagicMock(spec=UserManager)
        self.mock_progress_tracker = MagicMock(spec=ProgressTracker)
        self.mock_challenge_manager = MagicMock(spec=ChallengeManager)

        # Create a ProfileWidget instance with all required mock managers
        self.profile_widget = ProfileWidget(
            self.mock_user_manager,
            self.mock_progress_tracker,
            self.mock_challenge_manager,
        )

        # Sample user data
        self.sample_user = {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "bio": "Test bio",
            "avatar": None,
            "registration_date": "2023-01-01 12:00:00",
            "ai_consent_given": None,
        }

    def test_set_user(self):
        """Test setting the current user."""
        # Set the user
        self.profile_widget.set_user(self.sample_user)

        # Check that the user was set correctly
        self.assertEqual(self.profile_widget.current_user, self.sample_user)
        self.assertEqual(self.profile_widget.username_label.text(), "test_user")
        self.assertEqual(self.profile_widget.reg_date_label.text(), "2023-01-01")
        self.assertEqual(self.profile_widget.bio_display_label.text(), "Test bio")

    def test_set_user_none(self):
        """Test setting the current user to None."""
        # Set the user to None
        self.profile_widget.set_user(None)

        # Check that the user was cleared correctly
        self.assertIsNone(self.profile_widget.current_user)
        self.assertEqual(self.profile_widget.username_label.text(), "N/A")
        self.assertEqual(self.profile_widget.reg_date_label.text(), "N/A")
        self.assertEqual(self.profile_widget.bio_display_label.text(), "请先登录")

    def test_toggle_bio_edit(self):
        """Test toggling between displaying and editing the bio."""
        # Set the user
        self.profile_widget.set_user(self.sample_user)

        # Check initial state (display mode)
        self.assertTrue(self.profile_widget.bio_display_label.isVisible())
        self.assertTrue(self.profile_widget.edit_bio_button.isVisible())
        self.assertFalse(self.profile_widget.bio_edit.isVisible())
        self.assertFalse(self.profile_widget.save_bio_button.isVisible())
        self.assertFalse(self.profile_widget.cancel_bio_button.isVisible())

        # Toggle to edit mode
        self.profile_widget.toggle_bio_edit(True)

        # Check edit mode
        self.assertFalse(self.profile_widget.bio_display_label.isVisible())
        self.assertFalse(self.profile_widget.edit_bio_button.isVisible())
        self.assertTrue(self.profile_widget.bio_edit.isVisible())
        self.assertTrue(self.profile_widget.save_bio_button.isVisible())
        self.assertTrue(self.profile_widget.cancel_bio_button.isVisible())

        # Toggle back to display mode
        self.profile_widget.toggle_bio_edit(False)

        # Check display mode
        self.assertTrue(self.profile_widget.bio_display_label.isVisible())
        self.assertTrue(self.profile_widget.edit_bio_button.isVisible())
        self.assertFalse(self.profile_widget.bio_edit.isVisible())
        self.assertFalse(self.profile_widget.save_bio_button.isVisible())
        self.assertFalse(self.profile_widget.cancel_bio_button.isVisible())

    def test_save_bio(self):
        """Test saving the bio."""
        # Set the user
        self.profile_widget.set_user(self.sample_user)

        # Configure the mock to return True for the update
        self.mock_user_manager.update_bio.return_value = True

        # Set the bio text
        self.profile_widget.bio_edit.setText("New bio")

        # Save the bio
        with patch(
            "frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation"
        ) as mock_show_info:
            self.profile_widget.save_bio()

        # Check that the bio was updated
        self.assertEqual(self.profile_widget.bio_display_label.text(), "New bio")

        # Check that the mock was called correctly
        self.mock_user_manager.update_bio.assert_called_once_with(1, "New bio")
        mock_show_info.assert_called_once()

    def test_toggle_ai_consent_true(self):
        """Test toggling AI consent to True."""
        # Set the user
        self.profile_widget.set_user(self.sample_user)

        # Configure the mock to return True for the update
        self.mock_user_manager.set_ai_consent.return_value = True

        # Toggle AI consent to True
        with patch(
            "frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation"
        ) as mock_show_info:
            self.profile_widget.toggle_ai_consent(Qt.Checked)

        # Check that the user was updated
        self.assertTrue(self.profile_widget.current_user["ai_consent_given"])

        # Check that the mocks were called correctly
        self.mock_user_manager.set_ai_consent.assert_called_once_with(1, True)
        mock_show_info.assert_called_once()

    def test_toggle_ai_consent_false(self):
        """Test toggling AI consent to False."""
        # Set the user with AI consent initially True
        user_with_consent = self.sample_user.copy()
        user_with_consent["ai_consent_given"] = True
        self.profile_widget.set_user(user_with_consent)

        # Configure the mock to return True for the update
        self.mock_user_manager.set_ai_consent.return_value = True

        # Toggle AI consent to False
        with patch(
            "frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation"
        ) as mock_show_info:
            self.profile_widget.toggle_ai_consent(Qt.Unchecked)

        # Check that the user was updated
        self.assertFalse(self.profile_widget.current_user["ai_consent_given"])

        # Check that the mocks were called correctly
        self.mock_user_manager.set_ai_consent.assert_called_once_with(1, False)
        mock_show_info.assert_called_once()

    def test_toggle_ai_consent_no_user(self):
        """Test toggling AI consent when no user is logged in."""
        # Set the user to None
        self.profile_widget.set_user(None)

        # Toggle AI consent
        self.profile_widget.toggle_ai_consent(Qt.Checked)

        # Check that the mock was not called
        self.mock_user_manager.set_ai_consent.assert_not_called()

    def test_toggle_ai_consent_update_failed(self):
        """Test toggling AI consent when the update fails."""
        # Set the user
        self.profile_widget.set_user(self.sample_user)

        # Configure the mock to return False for the update
        self.mock_user_manager.set_ai_consent.return_value = False

        # Toggle AI consent
        with patch(
            "frontend.widgets.animated_message_box.AnimatedMessageBox.showWarning"
        ) as mock_show_warning:
            self.profile_widget.toggle_ai_consent(Qt.Checked)

        # Check that the user was not updated
        self.assertIsNone(self.profile_widget.current_user["ai_consent_given"])

        # Check that the mocks were called correctly
        self.mock_user_manager.set_ai_consent.assert_called_once_with(1, True)
        mock_show_warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
