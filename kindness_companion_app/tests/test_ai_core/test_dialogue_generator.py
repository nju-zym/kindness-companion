import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.dialogue_generator import generate_pet_dialogue, _call_dialogue_api

class TestDialogueGenerator(unittest.TestCase):
    """Test cases for the dialogue_generator module."""

    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to avoid polluting test output
        logging.basicConfig(level=logging.CRITICAL)

        # Sample event data for testing
        self.check_in_event = {
            'challenge_id': 1,
            'challenge_title': 'Daily Smile'
        }

        self.reflection_event = {
            'text': 'Feeling great after helping someone today!',
            'analyzed_emotion': 'positive'
        }

        self.user_message_event = {
            'message': 'Hello, how are you today?',
            'analyzed_emotion': 'neutral'
        }

        # Sample API response
        self.sample_api_response = "真棒！你完成了'Daily Smile'挑战，继续保持这种善意的行动！"

    @patch('ai_core.dialogue_generator._call_dialogue_api')
    def test_generate_pet_dialogue_check_in(self, mock_call_api):
        """Test generating dialogue for a check-in event."""
        # Configure mock
        mock_call_api.return_value = self.sample_api_response

        # Call the function
        result = generate_pet_dialogue(1, 'check_in', self.check_in_event)

        # Verify the result
        self.assertEqual(result, self.sample_api_response)

        # Verify the mock was called with a prompt containing the challenge title
        mock_call_api.assert_called_once()
        prompt = mock_call_api.call_args[0][0]
        self.assertIn('Daily Smile', prompt)

    @patch('ai_core.dialogue_generator._call_dialogue_api')
    def test_generate_pet_dialogue_reflection(self, mock_call_api):
        """Test generating dialogue for a reflection event."""
        # Configure mock
        mock_call_api.return_value = "很高兴听到你有这么积极的体验！继续保持这种善意的心态！"

        # Call the function
        result = generate_pet_dialogue(1, 'reflection_added', self.reflection_event)

        # Verify the result
        self.assertEqual(result, "很高兴听到你有这么积极的体验！继续保持这种善意的心态！")

        # Verify the mock was called with a prompt containing the reflection text and emotion
        mock_call_api.assert_called_once()
        prompt = mock_call_api.call_args[0][0]
        self.assertIn('Feeling great', prompt)
        self.assertIn('positive', prompt)

    @patch('ai_core.dialogue_generator._call_dialogue_api')
    def test_generate_pet_dialogue_api_error(self, mock_call_api):
        """Test generating dialogue when the API call fails."""
        # Configure mock to return None (API call failed)
        mock_call_api.return_value = None

        # Call the function
        result = generate_pet_dialogue(1, 'check_in', self.check_in_event)

        # Verify the result is a default message
        self.assertEqual(result, "... (宠物似乎正在安静地思考)")

        # Verify the mock was called
        mock_call_api.assert_called_once()

    @patch('ai_core.dialogue_generator._call_dialogue_api')
    def test_generate_pet_dialogue_empty_response(self, mock_call_api):
        """Test generating dialogue when the API returns an empty response."""
        # Configure mock to return an empty string
        mock_call_api.return_value = ""

        # Call the function
        result = generate_pet_dialogue(1, 'check_in', self.check_in_event)

        # Verify the result is a default message
        self.assertEqual(result, "... (宠物似乎正在安静地思考)")

        # Verify the mock was called
        mock_call_api.assert_called_once()

    @patch('ai_core.dialogue_generator.get_api_key')
    @patch('ai_core.dialogue_generator.make_api_request')
    def test_call_dialogue_api_success(self, mock_make_request, mock_get_api_key):
        """Test calling the dialogue API successfully."""
        # Configure mocks
        mock_get_api_key.return_value = "fake_api_key"
        mock_make_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }

        # Call the function
        result = _call_dialogue_api("Test prompt")

        # Verify the result
        self.assertEqual(result, "This is a test response")

        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()

    @patch('ai_core.dialogue_generator.get_api_key')
    def test_call_dialogue_api_no_api_key(self, mock_get_api_key):
        """Test API call when no API key is available."""
        # Configure mock to return None (no API key)
        mock_get_api_key.return_value = None

        # Call the function
        result = _call_dialogue_api("Test prompt")

        # Verify the result is None
        self.assertIsNone(result)

        # Verify the mock was called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')

    @patch('ai_core.dialogue_generator.get_api_key')
    @patch('ai_core.dialogue_generator.make_api_request')
    def test_call_dialogue_api_invalid_response(self, mock_make_request, mock_get_api_key):
        """Test handling an invalid API response."""
        # Configure mocks
        mock_get_api_key.return_value = "fake_api_key"
        mock_make_request.return_value = {"invalid": "response"}  # Missing 'choices'

        # Call the function
        result = _call_dialogue_api("Test prompt")

        # Verify the result is None
        self.assertIsNone(result)

        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()

    @patch('ai_core.dialogue_generator._call_dialogue_api')
    def test_generate_pet_dialogue_user_message(self, mock_call_api):
        """Test generating dialogue for a user message event."""
        # Configure mock
        mock_call_api.return_value = "你好！今天天气真不错，有什么我能帮你的吗？"

        # Call the function
        result = generate_pet_dialogue(1, 'user_message', self.user_message_event)

        # Verify the result
        self.assertEqual(result, "你好！今天天气真不错，有什么我能帮你的吗？")

        # Verify the mock was called with a prompt containing the user message and emotion
        mock_call_api.assert_called_once()
        prompt = mock_call_api.call_args[0][0]
        self.assertIn('Hello, how are you today?', prompt)
        self.assertIn('neutral', prompt)
        self.assertIn('direct message', prompt)  # Check that it mentions this is a direct message

if __name__ == '__main__':
    unittest.main()
