import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])

from frontend.pet_ui import PetWidget
from backend.user_manager import UserManager
from ai_core.pet_handler import handle_pet_event

class TestPetUI(unittest.TestCase):
    """Test cases for the PetWidget class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock UserManager
        self.mock_user_manager = MagicMock(spec=UserManager)
        
        # Create a PetWidget instance with the mock user manager
        self.pet_widget = PetWidget(self.mock_user_manager)
        
        # Sample user data
        self.sample_user = {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "ai_consent_given": True
        }
        
        # Sample pet response
        self.sample_pet_response = {
            "dialogue": "Hello! I'm your pet companion.",
            "suggested_animation": "happy",
            "emotion_detected": "positive"
        }
    
    def test_set_user(self):
        """Test setting the current user."""
        # Set the user
        self.pet_widget.set_user(self.sample_user)
        
        # Check that the user was set correctly
        self.assertEqual(self.pet_widget.current_user, self.sample_user)
        
        # Check that the pet is visible
        self.assertTrue(self.pet_widget.pet_container.isVisible())
        self.assertTrue(self.pet_widget.pet_label.isVisible())
        self.assertTrue(self.pet_widget.dialogue_label.isVisible())
    
    def test_set_user_none(self):
        """Test setting the current user to None."""
        # Set the user to None
        self.pet_widget.set_user(None)
        
        # Check that the user was cleared correctly
        self.assertIsNone(self.pet_widget.current_user)
        
        # Check that the pet is hidden
        self.assertFalse(self.pet_widget.pet_container.isVisible())
    
    def test_set_user_no_consent(self):
        """Test setting a user who has not given AI consent."""
        # Set a user with AI consent set to False
        user_without_consent = self.sample_user.copy()
        user_without_consent["ai_consent_given"] = False
        self.pet_widget.set_user(user_without_consent)
        
        # Check that the user was set correctly
        self.assertEqual(self.pet_widget.current_user, user_without_consent)
        
        # Check that the pet is hidden
        self.assertFalse(self.pet_widget.pet_container.isVisible())
    
    @patch('ai_core.pet_handler.handle_pet_event')
    def test_handle_check_in_event(self, mock_handle_event):
        """Test handling a check-in event."""
        # Configure the mock
        mock_handle_event.return_value = self.sample_pet_response
        
        # Set the user
        self.pet_widget.set_user(self.sample_user)
        
        # Handle a check-in event
        event_data = {
            "challenge_id": 1,
            "challenge_title": "Daily Smile"
        }
        self.pet_widget.handle_event("check_in", event_data)
        
        # Check that the pet dialogue was updated
        self.assertEqual(self.pet_widget.dialogue_label.text(), "Hello! I'm your pet companion.")
        
        # Check that the mock was called correctly
        mock_handle_event.assert_called_once_with(1, "check_in", event_data)
    
    @patch('ai_core.pet_handler.handle_pet_event')
    def test_handle_reflection_event(self, mock_handle_event):
        """Test handling a reflection event."""
        # Configure the mock
        mock_handle_event.return_value = self.sample_pet_response
        
        # Set the user
        self.pet_widget.set_user(self.sample_user)
        
        # Handle a reflection event
        event_data = {
            "text": "I felt great helping someone today!"
        }
        self.pet_widget.handle_event("reflection_added", event_data)
        
        # Check that the pet dialogue was updated
        self.assertEqual(self.pet_widget.dialogue_label.text(), "Hello! I'm your pet companion.")
        
        # Check that the mock was called correctly
        mock_handle_event.assert_called_once_with(1, "reflection_added", event_data)
    
    @patch('ai_core.pet_handler.handle_pet_event')
    def test_handle_event_no_user(self, mock_handle_event):
        """Test handling an event when no user is logged in."""
        # Set the user to None
        self.pet_widget.set_user(None)
        
        # Handle an event
        self.pet_widget.handle_event("check_in", {})
        
        # Check that the mock was not called
        mock_handle_event.assert_not_called()
    
    @patch('ai_core.pet_handler.handle_pet_event')
    def test_handle_event_no_consent(self, mock_handle_event):
        """Test handling an event when the user has not given AI consent."""
        # Set a user with AI consent set to False
        user_without_consent = self.sample_user.copy()
        user_without_consent["ai_consent_given"] = False
        self.pet_widget.set_user(user_without_consent)
        
        # Handle an event
        self.pet_widget.handle_event("check_in", {})
        
        # Check that the mock was not called
        mock_handle_event.assert_not_called()
    
    @patch('ai_core.pet_handler.handle_pet_event')
    def test_handle_event_error(self, mock_handle_event):
        """Test handling an event when an error occurs."""
        # Configure the mock to raise an exception
        mock_handle_event.side_effect = Exception("Test error")
        
        # Set the user
        self.pet_widget.set_user(self.sample_user)
        
        # Handle an event
        self.pet_widget.handle_event("check_in", {})
        
        # Check that the pet dialogue indicates an error
        self.assertTrue("出错了" in self.pet_widget.dialogue_label.text())
        
        # Check that the mock was called correctly
        mock_handle_event.assert_called_once()
    
    def test_show_ai_consent_dialog(self):
        """Test showing the AI consent dialog."""
        # Set a user with AI consent not set
        user_without_consent = self.sample_user.copy()
        user_without_consent["ai_consent_given"] = None
        
        # Mock the AI consent dialog
        with patch('frontend.widgets.ai_consent_dialog.AIConsentDialog.exec') as mock_exec:
            mock_exec.return_value = True  # User accepted
            
            # Configure the user manager mock
            self.mock_user_manager.set_ai_consent.return_value = True
            
            # Show the dialog
            self.pet_widget.show_ai_consent_dialog(user_without_consent)
        
        # Check that the user manager was called correctly
        self.mock_user_manager.set_ai_consent.assert_called_once_with(1, True)

if __name__ == '__main__':
    unittest.main()
