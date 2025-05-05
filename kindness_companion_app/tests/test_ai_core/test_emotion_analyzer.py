import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kindness_companion_app.ai_core.emotion_analyzer import (
    analyze_emotion_for_pet,
    _call_detailed_emotion_api,
    _call_basic_emotion_api,
    EMOTION_CATEGORIES
)

class TestEmotionAnalyzer(unittest.TestCase):
    """Test cases for the emotion_analyzer module."""

    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to avoid polluting test output
        logging.basicConfig(level=logging.CRITICAL)

        # Sample reflection texts for testing
        self.positive_text = "I felt really happy helping an elderly person cross the street today."
        self.negative_text = "I tried to help but was rejected, which made me feel sad."
        self.neutral_text = "I completed the daily task as planned."
        self.empty_text = ""

    @patch('kindness_companion_app.ai_core.emotion_analyzer._call_detailed_emotion_api')
    @patch('kindness_companion_app.ai_core.emotion_analyzer._call_basic_emotion_api')
    def test_analyze_emotion_for_pet(self, mock_basic_api, mock_detailed_api):
        """Test that analyze_emotion_for_pet returns the correct emotion and animation."""
        # Test with detailed emotion
        mock_detailed_api.return_value = 'happy'
        mock_basic_api.return_value = None

        emotion, animation = analyze_emotion_for_pet(1, self.positive_text)
        self.assertEqual(emotion, 'happy')
        self.assertEqual(animation, 'happy')

        # Test with detailed emotion that maps to 'excited'
        mock_detailed_api.return_value = 'excited'
        emotion, animation = analyze_emotion_for_pet(1, "I'm so excited about this!")
        self.assertEqual(emotion, 'excited')
        self.assertEqual(animation, 'excited')

        # Test with detailed emotion that maps to 'concerned'
        mock_detailed_api.return_value = 'sad'
        emotion, animation = analyze_emotion_for_pet(1, self.negative_text)
        self.assertEqual(emotion, 'sad')
        self.assertEqual(animation, 'concerned')

        # Test fallback to basic emotion
        mock_detailed_api.return_value = None
        mock_basic_api.return_value = 'positive'
        emotion, animation = analyze_emotion_for_pet(1, "This is a positive message.")
        self.assertEqual(emotion, 'positive')
        self.assertEqual(animation, 'happy')

        # Test with no emotion detected
        mock_detailed_api.return_value = None
        mock_basic_api.return_value = None
        emotion, animation = analyze_emotion_for_pet(1, self.neutral_text)
        self.assertIsNone(emotion)
        self.assertIsNone(animation)

        # Test with empty text
        emotion, animation = analyze_emotion_for_pet(1, self.empty_text)
        self.assertIsNone(emotion)
        self.assertIsNone(animation)

    @patch('kindness_companion_app.ai_core.emotion_analyzer.make_api_request')
    def test_call_detailed_emotion_api(self, mock_api_request):
        """Test that _call_detailed_emotion_api correctly processes API responses."""
        # Test successful API call with valid emotion
        mock_response = {
            'choices': [{'message': {'content': 'happy'}}]
        }
        mock_api_request.return_value = mock_response

        emotion = _call_detailed_emotion_api("I'm happy!")
        self.assertEqual(emotion, 'happy')

        # Test with emotion that needs to be extracted
        mock_response = {
            'choices': [{'message': {'content': 'The emotion is excited.'}}]
        }
        mock_api_request.return_value = mock_response

        emotion = _call_detailed_emotion_api("I'm excited!")
        self.assertEqual(emotion, 'excited')

        # Test with API failure
        mock_api_request.return_value = None
        emotion = _call_detailed_emotion_api("Test message")
        self.assertIsNone(emotion)

    @patch('kindness_companion_app.ai_core.emotion_analyzer.make_api_request')
    def test_call_basic_emotion_api(self, mock_api_request):
        """Test that _call_basic_emotion_api correctly processes API responses."""
        # Test successful API call with valid emotion
        mock_response = {
            'choices': [{'message': {'content': 'positive'}}]
        }
        mock_api_request.return_value = mock_response

        emotion = _call_basic_emotion_api("I'm happy!")
        self.assertEqual(emotion, 'positive')

        # Test with emotion that needs to be extracted
        mock_response = {
            'choices': [{'message': {'content': 'The text is negative.'}}]
        }
        mock_api_request.return_value = mock_response

        emotion = _call_basic_emotion_api("I'm sad.")
        self.assertEqual(emotion, 'negative')

        # Test with API failure
        mock_api_request.return_value = None
        emotion = _call_basic_emotion_api("Test message")
        self.assertIsNone(emotion)

    def test_emotion_categories(self):
        """Test that all emotions map to valid animations."""
        valid_animations = ['idle', 'happy', 'excited', 'concerned', 'confused']

        for emotion, animation in EMOTION_CATEGORIES.items():
            self.assertIn(animation, valid_animations,
                         f"Emotion '{emotion}' maps to invalid animation '{animation}'")

    @patch('kindness_companion_app.ai_core.emotion_analyzer._call_detailed_emotion_api')
    def test_analyze_api_error(self, mock_call_api):
        """Test handling an error during API call."""
        # Configure mock to raise an exception
        mock_call_api.side_effect = Exception("API error")

        # Call the function
        emotion, animation = analyze_emotion_for_pet(1, self.positive_text)

        # Verify the result is None
        self.assertIsNone(emotion)
        self.assertIsNone(animation)

        # Verify the mock was called correctly
        mock_call_api.assert_called_once_with(self.positive_text)

if __name__ == '__main__':
    unittest.main()
