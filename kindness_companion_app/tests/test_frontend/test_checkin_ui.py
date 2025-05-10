import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.checkin_ui import CheckinWidget
from backend.progress_tracker import ProgressTracker
from backend.challenge_manager import ChallengeManager

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])


@pytest.fixture
def mock_managers():
    """Create mock managers for testing."""
    progress_tracker = MagicMock(spec=ProgressTracker)
    challenge_manager = MagicMock(spec=ChallengeManager)

    # Configure challenge_manager to return sample challenges
    sample_challenges = [
        {
            "id": 1,
            "title": "每日微笑",
            "description": "对遇到的每个人微笑，传递善意",
            "category": "日常行为",
            "difficulty": 1,
        },
        {
            "id": 2,
            "title": "扶老助残",
            "description": "帮助老人或残障人士完成一项任务",
            "category": "社区服务",
            "difficulty": 2,
        },
    ]
    challenge_manager.get_user_challenges.return_value = sample_challenges

    # Configure progress_tracker to return sample data
    progress_tracker.get_streak.return_value = 3
    progress_tracker.check_in.return_value = True

    return {
        "progress_tracker": progress_tracker,
        "challenge_manager": challenge_manager,
    }


@pytest.fixture
def checkin_widget(mock_managers):
    """Create a CheckinWidget instance for testing."""
    widget = CheckinWidget(
        progress_tracker=mock_managers["progress_tracker"],
        challenge_manager=mock_managers["challenge_manager"],
    )

    # Yield the widget for the test
    yield widget

    # Clean up after the test
    widget.deleteLater()


def test_checkin_widget_initialization(checkin_widget, mock_managers):
    """Test that the checkin widget initializes correctly."""
    # Check that the managers were passed correctly
    assert checkin_widget.progress_tracker == mock_managers["progress_tracker"]
    assert checkin_widget.challenge_manager == mock_managers["challenge_manager"]

    # Check that the UI components were created
    assert checkin_widget.challenge_list is not None
    assert checkin_widget.notes_edit is not None
    assert checkin_widget.check_in_button is not None
    assert checkin_widget.calendar is not None
    assert checkin_widget.streak_container is not None
    assert checkin_widget.streak_label is not None


def test_set_user(checkin_widget, mock_managers):
    """Test setting the current user."""
    # Sample user data
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}

    # Set the user
    checkin_widget.set_user(sample_user)

    # Check that the user was set correctly
    assert checkin_widget.current_user == sample_user

    # Check that the challenges were loaded
    mock_managers["challenge_manager"].get_user_challenges.assert_called_once_with(1)

    # Check that the challenge list was populated
    assert checkin_widget.challenge_list.count() > 0


def test_load_checkable_challenges(checkin_widget, mock_managers):
    """Test loading checkable challenges."""
    # First, set a user
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Reset the mock to clear the call from set_user
    mock_managers["challenge_manager"].get_user_challenges.reset_mock()

    # Load checkable challenges
    checkin_widget.load_checkable_challenges()

    # Check that the challenges were loaded
    mock_managers["challenge_manager"].get_user_challenges.assert_called_once_with(1)

    # Check that the challenge list was populated
    assert checkin_widget.challenge_list.count() > 0

    # Check that the first challenge is selected
    assert checkin_widget.challenge_list.currentRow() == 0


def test_on_challenge_selected(checkin_widget, mock_managers):
    """Test handling challenge selection."""
    # First, set a user and load challenges
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Select a challenge
    checkin_widget.challenge_list.setCurrentRow(0)

    # Check that the calendar was updated
    mock_managers["progress_tracker"].get_streak.assert_called_with(1, 1)

    # Check that the streak label was updated
    assert checkin_widget.streak_label.text() == "当前连续打卡: 3 天"

    # Check that the streak container is visible
    assert checkin_widget.streak_container.isVisible()


@patch("frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation")
def test_check_in(mock_show_info, checkin_widget, mock_managers, qtbot):
    """Test checking in to a challenge."""
    # First, set a user and load challenges
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Select a challenge
    checkin_widget.challenge_list.setCurrentRow(0)

    # Enter some notes
    checkin_widget.notes_edit.setPlainText("Test notes")

    # Connect to the check_in_successful signal
    check_in_successful_called = False

    def on_check_in_successful():
        nonlocal check_in_successful_called
        check_in_successful_called = True

    checkin_widget.check_in_successful.connect(on_check_in_successful)

    # Click the check-in button
    qtbot.mouseClick(checkin_widget.check_in_button, Qt.MouseButton.LeftButton)

    # Check that the progress tracker was called correctly
    mock_managers["progress_tracker"].check_in.assert_called_once_with(
        1, 1, notes="Test notes"
    )

    # Check that the streak was updated
    mock_managers["progress_tracker"].get_streak.assert_called_with(1, 1)

    # Check that the success message was shown
    mock_show_info.assert_called_once()

    # Check that the check_in_successful signal was emitted
    assert check_in_successful_called


@patch("frontend.widgets.animated_message_box.AnimatedMessageBox.showWarning")
def test_check_in_no_challenge(mock_show_warning, checkin_widget, qtbot):
    """Test checking in when no challenge is selected."""
    # First, set a user but don't load any challenges
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Clear the challenge list
    checkin_widget.challenge_list.clear()

    # Click the check-in button
    qtbot.mouseClick(checkin_widget.check_in_button, Qt.MouseButton.LeftButton)

    # Check that a warning message was shown
    mock_show_warning.assert_called_once()


@patch("frontend.widgets.animated_message_box.AnimatedMessageBox.showWarning")
def test_check_in_no_user(mock_show_warning, checkin_widget, qtbot):
    """Test checking in when no user is logged in."""
    # Set the user to None
    checkin_widget.set_user(None)

    # Click the check-in button
    qtbot.mouseClick(checkin_widget.check_in_button, Qt.MouseButton.LeftButton)

    # Check that a warning message was shown
    mock_show_warning.assert_called_once()


@patch("frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation")
def test_check_in_failure(mock_show_info, checkin_widget, mock_managers, qtbot):
    """Test checking in when the check-in fails."""
    # Configure the progress_tracker to return failure
    mock_managers["progress_tracker"].check_in.return_value = False

    # First, set a user and load challenges
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Select a challenge
    checkin_widget.challenge_list.setCurrentRow(0)

    # Connect to the check_in_successful signal
    check_in_successful_called = False

    def on_check_in_successful():
        nonlocal check_in_successful_called
        check_in_successful_called = True

    checkin_widget.check_in_successful.connect(on_check_in_successful)

    # Click the check-in button
    qtbot.mouseClick(checkin_widget.check_in_button, Qt.MouseButton.LeftButton)

    # Check that the progress tracker was called correctly
    mock_managers["progress_tracker"].check_in.assert_called_once()

    # Check that the success message was not shown
    mock_show_info.assert_not_called()

    # Check that the check_in_successful signal was not emitted
    assert not check_in_successful_called


def test_update_calendar(checkin_widget, mock_managers):
    """Test updating the calendar."""
    # First, set a user and load challenges
    sample_user = {"id": 1, "username": "test_user", "email": "test@example.com"}
    checkin_widget.set_user(sample_user)

    # Select a challenge
    checkin_widget.challenge_list.setCurrentRow(0)

    # Update the calendar
    checkin_widget.calendar.update_calendar(1, 1)

    # Check that the calendar was updated
    # This is a basic check; in a real test, you would verify the calendar's internal state
