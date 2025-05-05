import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kindness_companion_app.ai_core.pet_handler import handle_pet_event

class TestPetHandlerEmotions(unittest.TestCase):
    """Test cases for the pet_handler module's emotion handling."""

    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to avoid polluting test output
        logging.basicConfig(level=logging.CRITICAL)
        
        # Sample event data for testing
        self.user_message_event = {'message': 'I am feeling happy today!'}
        self.reflection_event = {'text': 'I felt sad after failing to help someone.'}
        self.check_in_event = {'challenge_id': 1, 'challenge_title': 'Daily Kindness'}

    @patch('kindness_companion_app.ai_core.pet_handler.analyze_emotion_for_pet')
    @patch('kindness_companion_app.ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_user_message_with_emotion(self, mock_generate_dialogue, mock_analyze_emotion):
        """Test handling a user message with emotion analysis."""
        # Configure mocks
        mock_analyze_emotion.return_value = ('happy', 'happy')
        mock_generate_dialogue.return_value = "I'm glad you're feeling happy!"
        
        # Call the function
        result = handle_pet_event(1, 'user_message', self.user_message_event)
        
        # Verify the result
        self.assertEqual(result['dialogue'], "I'm glad you're feeling happy!")
        self.assertEqual(result['suggested_animation'], 'happy')
        self.assertEqual(result['emotion_detected'], 'happy')
        
        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.user_message_event['message'])
        mock_generate_dialogue.assert_called_once()

    @patch('kindness_companion_app.ai_core.pet_handler.analyze_emotion_for_pet')
    @patch('kindness_companion_app.ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_reflection_with_emotion(self, mock_generate_dialogue, mock_analyze_emotion):
        """Test handling a reflection with emotion analysis."""
        # Configure mocks
        mock_analyze_emotion.return_value = ('sad', 'concerned')
        mock_generate_dialogue.return_value = "I'm sorry to hear that you felt sad."
        
        # Call the function
        result = handle_pet_event(1, 'reflection_added', self.reflection_event)
        
        # Verify the result
        self.assertEqual(result['dialogue'], "I'm sorry to hear that you felt sad.")
        self.assertEqual(result['suggested_animation'], 'concerned')
        self.assertEqual(result['emotion_detected'], 'sad')
        
        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.reflection_event['text'])
        mock_generate_dialogue.assert_called_once()

    @patch('kindness_companion_app.ai_core.pet_handler.analyze_emotion_for_pet')
    @patch('kindness_companion_app.ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_check_in_without_emotion_analysis(self, mock_generate_dialogue, mock_analyze_emotion):
        """Test handling a check-in event (which doesn't use emotion analysis)."""
        # Configure mocks
        mock_analyze_emotion.return_value = (None, None)  # Should not be called
        mock_generate_dialogue.return_value = "Great job checking in!"
        
        # Call the function
        result = handle_pet_event(1, 'check_in', self.check_in_event)
        
        # Verify the result
        self.assertEqual(result['dialogue'], "Great job checking in!")
        self.assertEqual(result['suggested_animation'], 'happy')  # Default for check-in
        self.assertIsNone(result['emotion_detected'])
        
        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_not_called()
        mock_generate_dialogue.assert_called_once()

    @patch('kindness_companion_app.ai_core.pet_handler.analyze_emotion_for_pet')
    @patch('kindness_companion_app.ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_user_message_with_detailed_emotion(self, mock_generate_dialogue, mock_analyze_emotion):
        """Test handling a user message with detailed emotion analysis."""
        # Configure mocks for different emotions
        emotions_and_animations = [
            ('excited', 'excited'),
            ('joyful', 'excited'),
            ('sad', 'concerned'),
            ('anxious', 'concerned'),
            ('confused', 'confused'),
            ('surprised', 'confused'),
            ('calm', 'idle'),
            ('reflective', 'idle')
        ]
        
        for emotion, expected_animation in emotions_and_animations:
            mock_analyze_emotion.reset_mock()
            mock_generate_dialogue.reset_mock()
            
            mock_analyze_emotion.return_value = (emotion, expected_animation)
            mock_generate_dialogue.return_value = f"I see you're feeling {emotion}."
            
            # Call the function
            result = handle_pet_event(1, 'user_message', {'message': f"I feel {emotion}."})
            
            # Verify the result
            self.assertEqual(result['dialogue'], f"I see you're feeling {emotion}.")
            self.assertEqual(result['suggested_animation'], expected_animation)
            self.assertEqual(result['emotion_detected'], emotion)
            
            # Verify the mocks were called correctly
            mock_analyze_emotion.assert_called_once()
            mock_generate_dialogue.assert_called_once()

if __name__ == '__main__':
    unittest.main()
