import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.emotion_analyzer import analyze_emotion_for_pet, _call_emotion_api

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

    @patch('ai_core.emotion_analyzer._call_emotion_api')
    def test_analyze_positive_emotion(self, mock_call_api):
        """Test analyzing a positive emotion."""
        # Configure mock
        mock_call_api.return_value = "positive"
        
        # Call the function
        result = analyze_emotion_for_pet(1, self.positive_text)
        
        # Verify the result
        self.assertEqual(result, "positive")
        
        # Verify the mock was called correctly
        mock_call_api.assert_called_once_with(self.positive_text)
    
    @patch('ai_core.emotion_analyzer._call_emotion_api')
    def test_analyze_negative_emotion(self, mock_call_api):
        """Test analyzing a negative emotion."""
        # Configure mock
        mock_call_api.return_value = "negative"
        
        # Call the function
        result = analyze_emotion_for_pet(1, self.negative_text)
        
        # Verify the result
        self.assertEqual(result, "negative")
        
        # Verify the mock was called correctly
        mock_call_api.assert_called_once_with(self.negative_text)
    
    @patch('ai_core.emotion_analyzer._call_emotion_api')
    def test_analyze_neutral_emotion(self, mock_call_api):
        """Test analyzing a neutral emotion."""
        # Configure mock
        mock_call_api.return_value = "neutral"
        
        # Call the function
        result = analyze_emotion_for_pet(1, self.neutral_text)
        
        # Verify the result
        self.assertEqual(result, "neutral")
        
        # Verify the mock was called correctly
        mock_call_api.assert_called_once_with(self.neutral_text)
    
    def test_analyze_empty_text(self):
        """Test analyzing an empty text."""
        # Call the function with empty text
        result = analyze_emotion_for_pet(1, self.empty_text)
        
        # Verify the result is None
        self.assertIsNone(result)
    
    @patch('ai_core.emotion_analyzer._call_emotion_api')
    def test_analyze_api_error(self, mock_call_api):
        """Test handling an error during API call."""
        # Configure mock to raise an exception
        mock_call_api.side_effect = Exception("API error")
        
        # Call the function
        result = analyze_emotion_for_pet(1, self.positive_text)
        
        # Verify the result is None
        self.assertIsNone(result)
        
        # Verify the mock was called correctly
        mock_call_api.assert_called_once_with(self.positive_text)
    
    @patch('ai_core.emotion_analyzer.get_api_key')
    @patch('ai_core.emotion_analyzer.make_api_request')
    def test_call_emotion_api_success(self, mock_make_request, mock_get_api_key):
        """Test calling the emotion API successfully."""
        # Configure mocks
        mock_get_api_key.return_value = "fake_api_key"
        mock_make_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "positive"
                    }
                }
            ]
        }
        
        # Call the function
        result = _call_emotion_api("Test text")
        
        # Verify the result
        self.assertEqual(result, "positive")
        
        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()
    
    @patch('ai_core.emotion_analyzer.get_api_key')
    def test_call_emotion_api_no_api_key(self, mock_get_api_key):
        """Test API call when no API key is available."""
        # Configure mock to return None (no API key)
        mock_get_api_key.return_value = None
        
        # Call the function
        result = _call_emotion_api("Test text")
        
        # Verify the result is None
        self.assertIsNone(result)
        
        # Verify the mock was called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
    
    @patch('ai_core.emotion_analyzer.get_api_key')
    @patch('ai_core.emotion_analyzer.make_api_request')
    def test_call_emotion_api_invalid_response(self, mock_make_request, mock_get_api_key):
        """Test handling an invalid API response."""
        # Configure mocks
        mock_get_api_key.return_value = "fake_api_key"
        mock_make_request.return_value = {"invalid": "response"}  # Missing 'choices'
        
        # Call the function
        result = _call_emotion_api("Test text")
        
        # Verify the result is None
        self.assertIsNone(result)
        
        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()
    
    @patch('ai_core.emotion_analyzer.get_api_key')
    @patch('ai_core.emotion_analyzer.make_api_request')
    def test_call_emotion_api_invalid_emotion(self, mock_make_request, mock_get_api_key):
        """Test handling an invalid emotion in the API response."""
        # Configure mocks
        mock_get_api_key.return_value = "fake_api_key"
        mock_make_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "happy"  # Not one of the expected values (positive, negative, neutral)
                    }
                }
            ]
        }
        
        # Call the function
        result = _call_emotion_api("Test text")
        
        # Verify the result is None
        self.assertIsNone(result)
        
        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()

if __name__ == '__main__':
    unittest.main()
