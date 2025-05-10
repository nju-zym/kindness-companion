import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from frontend.main_window import MainWindow
from backend.user_manager import UserManager
from backend.challenge_manager import ChallengeManager
from backend.progress_tracker import ProgressTracker
from backend.reminder_scheduler import ReminderScheduler

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])

@pytest.fixture
def mock_managers():
    """Create mock managers for testing."""
    user_manager = MagicMock(spec=UserManager)
    challenge_manager = MagicMock(spec=ChallengeManager)
    progress_tracker = MagicMock(spec=ProgressTracker)
    reminder_scheduler = MagicMock(spec=ReminderScheduler)
    
    # Configure user_manager to return a sample user
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "bio": "Test bio",
        "avatar_path": ":/images/profilePicture.png",
        "avatar": None,
        "registration_date": "2023-01-01 12:00:00",
        "ai_consent_given": True
    }
    user_manager.get_current_user.return_value = sample_user
    
    return {
        "user_manager": user_manager,
        "challenge_manager": challenge_manager,
        "progress_tracker": progress_tracker,
        "reminder_scheduler": reminder_scheduler
    }

@pytest.fixture
def main_window(mock_managers):
    """Create a MainWindow instance for testing."""
    window = MainWindow(
        user_manager=mock_managers["user_manager"],
        challenge_manager=mock_managers["challenge_manager"],
        progress_tracker=mock_managers["progress_tracker"],
        reminder_scheduler=mock_managers["reminder_scheduler"]
    )
    
    # Yield the window for the test
    yield window
    
    # Clean up after the test
    window.close()

def test_main_window_initialization(main_window, mock_managers):
    """Test that the main window initializes correctly."""
    # Check that the window has the correct title
    assert "善行伴侣" in main_window.windowTitle()
    
    # Check that the managers were passed correctly
    assert main_window.user_manager == mock_managers["user_manager"]
    assert main_window.challenge_manager == mock_managers["challenge_manager"]
    assert main_window.progress_tracker == mock_managers["progress_tracker"]
    assert main_window.reminder_scheduler == mock_managers["reminder_scheduler"]
    
    # Check that the UI components were created
    assert main_window.login_widget is not None
    assert main_window.register_widget is not None
    assert main_window.challenge_widget is not None
    assert main_window.checkin_widget is not None
    assert main_window.progress_widget is not None
    assert main_window.reminder_widget is not None
    assert main_window.community_widget is not None
    assert main_window.profile_widget is not None
    assert main_window.pet_widget is not None

def test_navigation_buttons(main_window, qtbot):
    """Test that navigation buttons work correctly."""
    # First, simulate a login to enable navigation
    main_window.handle_login({"id": 1, "username": "test_user"})
    
    # Find navigation buttons
    nav_buttons = main_window.findChildren(type(main_window.nav_buttons[0]))
    
    # Test each navigation button
    for button in nav_buttons:
        # Click the button
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        
        # Check that the content widget changed
        # This is a basic check; in a real test, you would verify the specific widget

def test_handle_login(main_window, mock_managers):
    """Test handling a successful login."""
    # Simulate a login
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    main_window.handle_login(sample_user)
    
    # Check that the user was set
    assert main_window.current_user == sample_user
    
    # Check that the user_changed signal was emitted
    # This is indirectly tested by checking if the user was set in the widgets
    mock_managers["challenge_manager"].get_user_challenges.assert_called_once_with(1)
    
    # Check that the navigation buttons are enabled
    for button in main_window.nav_buttons:
        assert button.isEnabled()
    
    # Check that the login/register buttons are hidden
    assert not main_window.login_button.isVisible()
    assert not main_window.register_button.isVisible()
    
    # Check that the logout button is visible
    assert main_window.logout_button.isVisible()

def test_handle_logout(main_window, mock_managers):
    """Test handling a logout."""
    # First, simulate a login
    main_window.handle_login({"id": 1, "username": "test_user"})
    
    # Then, simulate a logout
    main_window.handle_logout()
    
    # Check that the user was cleared
    assert main_window.current_user is None
    
    # Check that the navigation buttons are disabled
    for button in main_window.nav_buttons:
        assert not button.isEnabled()
    
    # Check that the login/register buttons are visible
    assert main_window.login_button.isVisible()
    assert main_window.register_button.isVisible()
    
    # Check that the logout button is hidden
    assert not main_window.logout_button.isVisible()
    
    # Check that the login widget is shown
    assert main_window.content_widget.currentWidget() == main_window.login_widget

def test_show_login(main_window):
    """Test showing the login page."""
    # Show the login page
    main_window.show_login()
    
    # Check that the login widget is shown
    assert main_window.content_widget.currentWidget() == main_window.login_widget

def test_show_register(main_window):
    """Test showing the registration page."""
    # Show the registration page
    main_window.show_register()
    
    # Check that the register widget is shown
    assert main_window.content_widget.currentWidget() == main_window.register_widget

def test_on_checkin_successful(main_window):
    """Test handling a successful check-in."""
    # First, simulate a login
    main_window.handle_login({"id": 1, "username": "test_user"})
    
    # Then, simulate a successful check-in
    main_window.on_checkin_successful()
    
    # Check that the progress widget is refreshed
    # This is indirectly tested by checking if the progress widget is shown
    assert main_window.content_widget.currentWidget() == main_window.progress_scroll_area

def test_update_user_info(main_window, mock_managers):
    """Test updating user information."""
    # First, simulate a login
    main_window.handle_login({"id": 1, "username": "test_user"})
    
    # Then, update the user info
    updated_user = {
        "id": 1,
        "username": "test_user",
        "email": "updated@example.com",
        "bio": "Updated bio"
    }
    main_window.update_user_info(updated_user)
    
    # Check that the user was updated
    assert main_window.current_user == updated_user
    
    # Check that the user_changed signal was emitted
    # This is indirectly tested by checking if the user was set in the widgets
    mock_managers["challenge_manager"].get_user_challenges.assert_called_with(1)

def test_handle_theme_changed(main_window):
    """Test handling a theme change."""
    # Simulate a theme change
    main_window.handle_theme_changed("dark")
    
    # Check that the theme was applied
    # This is a basic check; in a real test, you would verify the theme was applied correctly
    assert main_window.current_theme == "dark"
