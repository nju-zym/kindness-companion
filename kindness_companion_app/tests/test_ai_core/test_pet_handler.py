import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.pet_handler import handle_pet_event

class TestPetHandler(unittest.TestCase):
    """Test cases for the pet_handler module."""

    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to avoid polluting test output
        logging.basicConfig(level=logging.CRITICAL)

        # Sample event data for testing
        self.check_in_event = {
            'challenge_id': 1,
            'challenge_title': 'Daily Smile'
        }

        self.reflection_event_pos = {
            'text': 'Feeling great after helping someone today!'
        }

        self.reflection_event_neg = {
            'text': 'Felt a bit down, but I tried my best.'
        }

        self.user_message_event = {
            'message': 'Hello, how are you today?'
        }

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_check_in_event(self, mock_generate_dialogue):
        """Test handling a check-in event."""
        # Configure mock
        mock_generate_dialogue.return_value = "Great job checking in!"

        # Call the function
        result = handle_pet_event(1, 'check_in', self.check_in_event)

        # Verify the result
        self.assertEqual(result['dialogue'], "Great job checking in!")
        self.assertEqual(result['suggested_animation'], 'happy')  # Check-ins should suggest 'happy' animation

        # Verify the mock was called correctly
        mock_generate_dialogue.assert_called_once_with(1, 'check_in', self.check_in_event)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_positive_reflection_event(self, mock_analyze_emotion, mock_generate_dialogue):
        """Test handling a positive reflection event."""
        # Configure mocks
        mock_analyze_emotion.return_value = ('positive', 'excited')
        mock_generate_dialogue.return_value = "I'm so happy to hear that!"

        # Call the function
        result = handle_pet_event(1, 'reflection_added', self.reflection_event_pos)

        # Verify the result
        self.assertEqual(result['dialogue'], "I'm so happy to hear that!")
        self.assertEqual(result['emotion_detected'], 'positive')
        self.assertEqual(result['suggested_animation'], 'excited')  # Positive reflections should suggest 'excited'

        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.reflection_event_pos['text'])
        # Check that the emotion was added to the context for dialogue generation
        dialogue_context = self.reflection_event_pos.copy()
        dialogue_context['analyzed_emotion'] = 'positive'
        dialogue_context['suggested_animation'] = 'excited'
        mock_generate_dialogue.assert_called_once_with(1, 'reflection_added', dialogue_context)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_negative_reflection_event(self, mock_analyze_emotion, mock_generate_dialogue):
        """Test handling a negative reflection event."""
        # Configure mocks
        mock_analyze_emotion.return_value = ('negative', 'concerned')
        mock_generate_dialogue.return_value = "I understand it was tough, but you did great!"

        # Call the function
        result = handle_pet_event(1, 'reflection_added', self.reflection_event_neg)

        # Verify the result
        self.assertEqual(result['dialogue'], "I understand it was tough, but you did great!")
        self.assertEqual(result['emotion_detected'], 'negative')
        self.assertEqual(result['suggested_animation'], 'concerned')  # Negative reflections should suggest 'concerned'

        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.reflection_event_neg['text'])
        # Check that the emotion was added to the context for dialogue generation
        dialogue_context = self.reflection_event_neg.copy()
        dialogue_context['analyzed_emotion'] = 'negative'
        dialogue_context['suggested_animation'] = 'concerned'
        mock_generate_dialogue.assert_called_once_with(1, 'reflection_added', dialogue_context)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_reflection_event_no_emotion(self, mock_analyze_emotion, mock_generate_dialogue):
        """Test handling a reflection event when emotion analysis fails."""
        # Configure mocks
        mock_analyze_emotion.return_value = (None, None)  # Emotion analysis failed
        mock_generate_dialogue.return_value = "Thanks for sharing your thoughts!"

        # Call the function
        result = handle_pet_event(1, 'reflection_added', self.reflection_event_pos)

        # Verify the result
        self.assertEqual(result['dialogue'], "Thanks for sharing your thoughts!")
        self.assertIsNone(result['emotion_detected'])
        # The default animation for reflection events with no emotion is now 'happy'
        self.assertEqual(result['suggested_animation'], 'happy')

        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.reflection_event_pos['text'])
        # Check that no emotion was added to the context for dialogue generation
        mock_generate_dialogue.assert_called_once_with(1, 'reflection_added', self.reflection_event_pos)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    def test_handle_dialogue_generation_error(self, mock_generate_dialogue):
        """Test handling an error during dialogue generation."""
        # Configure mock to raise an exception
        mock_generate_dialogue.side_effect = Exception("API error")

        # Call the function
        result = handle_pet_event(1, 'check_in', self.check_in_event)

        # Verify the result contains a default message
        self.assertEqual(result['dialogue'], "... (The pet seems lost in thought)")
        # The default animation for errors is now 'confused'
        self.assertEqual(result['suggested_animation'], 'confused')

        # Verify the mock was called correctly
        mock_generate_dialogue.assert_called_once_with(1, 'check_in', self.check_in_event)

    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_emotion_analysis_error(self, mock_analyze_emotion):
        """Test handling an error during emotion analysis."""
        # Configure mock to raise an exception
        mock_analyze_emotion.side_effect = Exception("API error")

        # We need to patch generate_pet_dialogue as well to avoid actual API calls
        with patch('ai_core.pet_handler.generate_pet_dialogue') as mock_generate_dialogue:
            mock_generate_dialogue.return_value = "Thanks for sharing!"

            # Call the function
            result = handle_pet_event(1, 'reflection_added', self.reflection_event_pos)

            # Verify the result doesn't contain emotion data
            self.assertEqual(result['dialogue'], "Thanks for sharing!")
            self.assertIsNone(result['emotion_detected'])
            # The default animation is now 'happy' for reflection events with no emotion
            self.assertEqual(result['suggested_animation'], 'happy')

            # Verify the mocks were called correctly
            mock_analyze_emotion.assert_called_once_with(1, self.reflection_event_pos['text'])
            mock_generate_dialogue.assert_called_once_with(1, 'reflection_added', self.reflection_event_pos)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_user_message_event(self, mock_analyze_emotion, mock_generate_dialogue):
        """Test handling a user message event."""
        # Configure mocks
        mock_analyze_emotion.return_value = ('positive', 'excited')
        mock_generate_dialogue.return_value = "你好！很高兴和你聊天。"

        # Call the function
        result = handle_pet_event(1, 'user_message', self.user_message_event)

        # Verify the result
        self.assertEqual(result['dialogue'], "你好！很高兴和你聊天。")
        self.assertEqual(result['emotion_detected'], 'positive')
        self.assertEqual(result['suggested_animation'], 'excited')  # Positive user messages should suggest 'excited'

        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.user_message_event['message'])
        # Check that the emotion was added to the context for dialogue generation
        dialogue_context = self.user_message_event.copy()
        dialogue_context['analyzed_emotion'] = 'positive'
        dialogue_context['suggested_animation'] = 'excited'
        mock_generate_dialogue.assert_called_once_with(1, 'user_message', dialogue_context)

    @patch('ai_core.pet_handler.generate_pet_dialogue')
    @patch('ai_core.pet_handler.analyze_emotion_for_pet')
    def test_handle_user_message_no_emotion(self, mock_analyze_emotion, mock_generate_dialogue):
        """Test handling a user message when emotion analysis returns None."""
        # Configure mocks
        mock_analyze_emotion.return_value = (None, None)
        mock_generate_dialogue.return_value = "你好！有什么我能帮你的吗？"

        # Call the function
        result = handle_pet_event(1, 'user_message', self.user_message_event)

        # Verify the result
        self.assertEqual(result['dialogue'], "你好！有什么我能帮你的吗？")
        self.assertIsNone(result['emotion_detected'])
        self.assertEqual(result['suggested_animation'], 'happy')  # Default for user messages with no emotion

        # Verify the mocks were called correctly
        mock_analyze_emotion.assert_called_once_with(1, self.user_message_event['message'])
        mock_generate_dialogue.assert_called_once_with(1, 'user_message', self.user_message_event)

if __name__ == '__main__':
    unittest.main()
