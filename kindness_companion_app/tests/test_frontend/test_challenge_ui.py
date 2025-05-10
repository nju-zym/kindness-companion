import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from frontend.challenge_ui import ChallengeListWidget, ChallengeCard
from backend.challenge_manager import ChallengeManager
from backend.progress_tracker import ProgressTracker

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])

@pytest.fixture
def mock_managers():
    """Create mock managers for testing."""
    challenge_manager = MagicMock(spec=ChallengeManager)
    progress_tracker = MagicMock(spec=ProgressTracker)
    
    # Configure challenge_manager to return sample challenges
    sample_challenges = [
        {
            "id": 1,
            "title": "每日微笑",
            "description": "对遇到的每个人微笑，传递善意",
            "category": "日常行为",
            "difficulty": 1
        },
        {
            "id": 2,
            "title": "扶老助残",
            "description": "帮助老人或残障人士完成一项任务",
            "category": "社区服务",
            "difficulty": 2
        }
    ]
    challenge_manager.get_all_challenges.return_value = sample_challenges
    challenge_manager.get_user_challenges.return_value = [sample_challenges[0]]
    challenge_manager.get_challenge_by_id.side_effect = lambda id: next((c for c in sample_challenges if c["id"] == id), None)
    
    # Configure progress_tracker to return sample streaks
    progress_tracker.get_streak.return_value = 3
    
    return {
        "challenge_manager": challenge_manager,
        "progress_tracker": progress_tracker
    }

@pytest.fixture
def challenge_widget(mock_managers):
    """Create a ChallengeListWidget instance for testing."""
    widget = ChallengeListWidget(
        challenge_manager=mock_managers["challenge_manager"],
        progress_tracker=mock_managers["progress_tracker"]
    )
    
    # Yield the widget for the test
    yield widget
    
    # Clean up after the test
    widget.deleteLater()

@pytest.fixture
def challenge_card():
    """Create a ChallengeCard instance for testing."""
    challenge = {
        "id": 1,
        "title": "每日微笑",
        "description": "对遇到的每个人微笑，传递善意",
        "category": "日常行为",
        "difficulty": 1
    }
    card = ChallengeCard(challenge, is_subscribed=False, streak=0)
    
    # Yield the card for the test
    yield card
    
    # Clean up after the test
    card.deleteLater()

def test_challenge_widget_initialization(challenge_widget, mock_managers):
    """Test that the challenge widget initializes correctly."""
    # Check that the managers were passed correctly
    assert challenge_widget.challenge_manager == mock_managers["challenge_manager"]
    assert challenge_widget.progress_tracker == mock_managers["progress_tracker"]
    
    # Check that the UI components were created
    assert challenge_widget.search_input is not None
    assert challenge_widget.category_combo is not None
    assert challenge_widget.difficulty_combo is not None
    assert challenge_widget.challenges_layout is not None

def test_set_user(challenge_widget, mock_managers):
    """Test setting the current user."""
    # Sample user data
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    
    # Set the user
    challenge_widget.set_user(sample_user)
    
    # Check that the user was set correctly
    assert challenge_widget.current_user == sample_user
    
    # Check that the challenges were loaded
    mock_managers["challenge_manager"].get_all_challenges.assert_called_once()
    mock_managers["challenge_manager"].get_user_challenges.assert_called_once_with(1)

def test_load_challenges(challenge_widget, mock_managers):
    """Test loading challenges."""
    # First, set a user
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    challenge_widget.set_user(sample_user)
    
    # Reset the mocks to clear the calls from set_user
    mock_managers["challenge_manager"].get_all_challenges.reset_mock()
    mock_managers["challenge_manager"].get_user_challenges.reset_mock()
    
    # Load challenges
    challenge_widget.load_challenges()
    
    # Check that the challenges were loaded
    mock_managers["challenge_manager"].get_all_challenges.assert_called_once()
    mock_managers["challenge_manager"].get_user_challenges.assert_called_once_with(1)
    
    # Check that challenge cards were created
    assert len(challenge_widget.challenge_cards) > 0

def test_filter_challenges(challenge_widget, qtbot):
    """Test filtering challenges."""
    # First, set a user and load challenges
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    challenge_widget.set_user(sample_user)
    
    # Get the initial number of visible challenge cards
    initial_visible_count = sum(1 for card in challenge_widget.challenge_cards.values() if card.isVisible())
    
    # Filter by category
    challenge_widget.category_combo.setCurrentText("日常行为")
    qtbot.mouseClick(challenge_widget.apply_filter_button, Qt.MouseButton.LeftButton)
    
    # Check that the challenges were filtered
    filtered_visible_count = sum(1 for card in challenge_widget.challenge_cards.values() if card.isVisible())
    assert filtered_visible_count <= initial_visible_count
    
    # Reset the filter
    challenge_widget.category_combo.setCurrentText("全部分类")
    qtbot.mouseClick(challenge_widget.apply_filter_button, Qt.MouseButton.LeftButton)
    
    # Check that all challenges are visible again
    reset_visible_count = sum(1 for card in challenge_widget.challenge_cards.values() if card.isVisible())
    assert reset_visible_count == initial_visible_count

@patch('PySide6.QtWidgets.QMessageBox.question')
def test_subscribe_to_challenge(mock_question, challenge_widget, mock_managers):
    """Test subscribing to a challenge."""
    # Configure the mock to return QMessageBox.Yes
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    # Configure the challenge_manager to return success
    mock_managers["challenge_manager"].subscribe_to_challenge.return_value = True
    
    # First, set a user
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    challenge_widget.set_user(sample_user)
    
    # Subscribe to a challenge
    challenge_widget.subscribe_to_challenge(2)  # ID of the second challenge
    
    # Check that the challenge manager was called correctly
    mock_managers["challenge_manager"].subscribe_to_challenge.assert_called_once_with(1, 2)
    
    # Check that the challenges were reloaded
    mock_managers["challenge_manager"].get_user_challenges.assert_called_with(1)

@patch('PySide6.QtWidgets.QMessageBox.question')
def test_unsubscribe_from_challenge(mock_question, challenge_widget, mock_managers):
    """Test unsubscribing from a challenge."""
    # Configure the mock to return QMessageBox.Yes
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    # Configure the challenge_manager to return success
    mock_managers["challenge_manager"].unsubscribe_from_challenge.return_value = True
    
    # First, set a user
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    challenge_widget.set_user(sample_user)
    
    # Unsubscribe from a challenge
    challenge_widget.unsubscribe_from_challenge(1)  # ID of the first challenge
    
    # Check that the challenge manager was called correctly
    mock_managers["challenge_manager"].unsubscribe_from_challenge.assert_called_once_with(1, 1)
    
    # Check that the challenges were reloaded
    mock_managers["challenge_manager"].get_user_challenges.assert_called_with(1)

@patch('PySide6.QtWidgets.QMessageBox.question')
def test_check_in_challenge(mock_question, challenge_widget, mock_managers):
    """Test checking in to a challenge."""
    # Configure the mock to return QMessageBox.Yes
    mock_question.return_value = QMessageBox.StandardButton.Yes
    
    # Configure the progress_tracker to return success
    mock_managers["progress_tracker"].check_in.return_value = True
    
    # First, set a user
    sample_user = {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com"
    }
    challenge_widget.set_user(sample_user)
    
    # Check in to a challenge
    challenge_widget.check_in_challenge(1)  # ID of the first challenge
    
    # Check that the progress tracker was called correctly
    mock_managers["progress_tracker"].check_in.assert_called_once_with(1, 1)
    
    # Check that the check_in_successful signal was emitted
    # This is difficult to test directly, but we can check that the mock was called

def test_challenge_card_initialization(challenge_card):
    """Test that the challenge card initializes correctly."""
    # Check that the challenge was set correctly
    assert challenge_card.challenge["id"] == 1
    assert challenge_card.challenge["title"] == "每日微笑"
    
    # Check that the UI components were created
    assert challenge_card.title_label is not None
    assert challenge_card.description_label is not None
    assert challenge_card.category_label is not None
    assert challenge_card.difficulty_label is not None
    assert challenge_card.subscribe_button is not None
    assert challenge_card.unsubscribe_button is not None
    assert challenge_card.check_in_button is not None

def test_challenge_card_update_ui(challenge_card, qtbot):
    """Test updating the challenge card UI."""
    # Check initial state
    assert not challenge_card.is_subscribed
    assert challenge_card.streak == 0
    assert challenge_card.subscribe_button.isVisible()
    assert not challenge_card.unsubscribe_button.isVisible()
    assert not challenge_card.check_in_button.isVisible()
    
    # Update the UI
    challenge_card.update_ui(is_subscribed=True, streak=3)
    
    # Check updated state
    assert challenge_card.is_subscribed
    assert challenge_card.streak == 3
    assert not challenge_card.subscribe_button.isVisible()
    assert challenge_card.unsubscribe_button.isVisible()
    assert challenge_card.check_in_button.isVisible()
    assert "连续打卡: 3 天" in challenge_card.streak_label.text()

def test_challenge_card_signals(challenge_card, qtbot):
    """Test that the challenge card signals are emitted correctly."""
    # Connect to the signals
    subscribe_called = False
    unsubscribe_called = False
    check_in_called = False
    
    def on_subscribe():
        nonlocal subscribe_called
        subscribe_called = True
    
    def on_unsubscribe():
        nonlocal unsubscribe_called
        unsubscribe_called = True
    
    def on_check_in():
        nonlocal check_in_called
        check_in_called = True
    
    challenge_card.subscribe_clicked.connect(on_subscribe)
    challenge_card.unsubscribe_clicked.connect(on_unsubscribe)
    challenge_card.check_in_clicked.connect(on_check_in)
    
    # Click the subscribe button
    qtbot.mouseClick(challenge_card.subscribe_button, Qt.MouseButton.LeftButton)
    assert subscribe_called
    
    # Update the UI to show the unsubscribe and check-in buttons
    challenge_card.update_ui(is_subscribed=True, streak=0)
    
    # Click the unsubscribe button
    qtbot.mouseClick(challenge_card.unsubscribe_button, Qt.MouseButton.LeftButton)
    assert unsubscribe_called
    
    # Click the check-in button
    qtbot.mouseClick(challenge_card.check_in_button, Qt.MouseButton.LeftButton)
    assert check_in_called
