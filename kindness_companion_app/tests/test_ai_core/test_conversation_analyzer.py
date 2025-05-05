"""
Test module for the conversation analyzer.
"""

import unittest
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kindness_companion_app.ai_core.conversation_analyzer import ConversationAnalyzer
from kindness_companion_app.backend.database_manager import DatabaseManager


class TestConversationAnalyzer(unittest.TestCase):
    """Test cases for the ConversationAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock database manager
        self.db_manager = MagicMock(spec=DatabaseManager)
        
        # Mock the execute_query method to return empty results
        self.db_manager.execute_query.return_value = []
        
        # Mock the execute_insert method to return a valid ID
        self.db_manager.execute_insert.return_value = 1
        
        # Mock the execute_update method to return success
        self.db_manager.execute_update.return_value = 1
        
        # Create a conversation analyzer with the mock database manager
        self.analyzer = ConversationAnalyzer(self.db_manager)
        
        # Sample user messages
        self.sample_messages = [
            "今天天气真好，我很开心！",
            "我完成了一个善行挑战，感觉很棒。",
            "希望明天也是美好的一天。"
        ]
        
        # Sample psychological profile
        self.sample_profile = {
            "personality_traits": {
                "extraversion": "high",
                "agreeableness": "high",
                "conscientiousness": "medium",
                "neuroticism": "low",
                "openness": "high"
            },
            "communication_preferences": {
                "formality": "casual",
                "verbosity": "moderate",
                "emotional_tone": "positive",
                "humor": "moderate"
            },
            "emotional_state": {
                "current_mood": "positive",
                "stress_level": "low"
            },
            "thinking_patterns": {
                "analytical": "medium",
                "creative": "high",
                "practical": "medium"
            },
            "confidence_score": 0.75,
            "last_updated": "2023-06-01T12:00:00"
        }

    def test_store_message(self):
        """Test storing a message in the conversation history."""
        # Call the method
        message_id = self.analyzer.store_message(user_id=1, message="Hello", is_user=True)
        
        # Check that execute_insert was called with the correct parameters
        self.db_manager.execute_insert.assert_called_once()
        args, kwargs = self.db_manager.execute_insert.call_args
        self.assertIn("INSERT INTO conversation_history", args[0])
        self.assertEqual(args[1][0], 1)  # user_id
        self.assertEqual(args[1][1], "Hello")  # message
        self.assertEqual(args[1][2], 1)  # is_user (True = 1)
        
        # Check the return value
        self.assertEqual(message_id, 1)

    def test_get_conversation_history(self):
        """Test retrieving conversation history."""
        # Mock the execute_query method to return sample messages
        sample_db_messages = [
            {"id": 1, "message": "Hello", "is_user": 1, "timestamp": "2023-06-01T12:00:00", "context_id": "ctx_1"},
            {"id": 2, "message": "Hi there!", "is_user": 0, "timestamp": "2023-06-01T12:01:00", "context_id": "ctx_1"}
        ]
        self.db_manager.execute_query.return_value = sample_db_messages
        
        # Call the method
        messages = self.analyzer.get_conversation_history(user_id=1, limit=10)
        
        # Check that execute_query was called with the correct parameters
        self.db_manager.execute_query.assert_called_once()
        args, kwargs = self.db_manager.execute_query.call_args
        self.assertIn("SELECT * FROM conversation_history", args[0])
        self.assertEqual(args[1][0], 1)  # user_id
        self.assertEqual(args[1][1], 10)  # limit
        
        # Check the return value format
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "Hi there!")

    @patch('kindness_companion_app.ai_core.conversation_analyzer.make_api_request')
    def test_analyze_user_psychology(self, mock_make_api_request):
        """Test analyzing user psychology."""
        # Mock the get_conversation_history method to return sample messages
        self.analyzer.get_conversation_history = MagicMock(return_value=[
            {"id": 1, "content": self.sample_messages[0], "role": "user"},
            {"id": 2, "content": "That's great!", "role": "assistant"},
            {"id": 3, "content": self.sample_messages[1], "role": "user"}
        ])
        
        # Mock the API response
        mock_make_api_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(self.sample_profile)
                    }
                }
            ]
        }
        
        # Mock the _store_psychological_profile method
        self.analyzer._store_psychological_profile = MagicMock(return_value=True)
        
        # Call the method
        profile = self.analyzer.analyze_user_psychology(user_id=1)
        
        # Check that get_conversation_history was called
        self.analyzer.get_conversation_history.assert_called_once_with(user_id=1, limit=50, context_id=None)
        
        # Check that make_api_request was called
        mock_make_api_request.assert_called_once()
        
        # Check that _store_psychological_profile was called with the correct profile
        self.analyzer._store_psychological_profile.assert_called_once_with(1, profile)
        
        # Check the return value
        self.assertEqual(profile["personality_traits"]["extraversion"], "high")
        self.assertEqual(profile["communication_preferences"]["formality"], "casual")
        self.assertEqual(profile["confidence_score"], 0.75)

    def test_get_dialogue_style(self):
        """Test getting dialogue style preferences."""
        # Mock the execute_query method to return sample style preferences
        sample_style = [
            {"formality_level": 4, "verbosity_level": 3, "empathy_level": 5, "humor_level": 2}
        ]
        self.db_manager.execute_query.return_value = sample_style
        
        # Call the method
        style = self.analyzer.get_dialogue_style(user_id=1)
        
        # Check that execute_query was called with the correct parameters
        self.db_manager.execute_query.assert_called_once()
        args, kwargs = self.db_manager.execute_query.call_args
        self.assertIn("SELECT formality_level, verbosity_level, empathy_level, humor_level", args[0])
        self.assertEqual(args[1][0], 1)  # user_id
        
        # Check the return value
        self.assertEqual(style["formality_level"], 4)
        self.assertEqual(style["verbosity_level"], 3)
        self.assertEqual(style["empathy_level"], 5)
        self.assertEqual(style["humor_level"], 2)
        
    def test_get_dialogue_style_default(self):
        """Test getting default dialogue style when no preferences exist."""
        # Mock the execute_query method to return empty results
        self.db_manager.execute_query.return_value = []
        
        # Call the method
        style = self.analyzer.get_dialogue_style(user_id=1)
        
        # Check the return value (should be default values)
        self.assertEqual(style["formality_level"], 3)
        self.assertEqual(style["verbosity_level"], 3)
        self.assertEqual(style["empathy_level"], 3)
        self.assertEqual(style["humor_level"], 3)

    @patch('kindness_companion_app.ai_core.conversation_analyzer.make_api_request')
    def test_generate_dialogue_with_style(self, mock_make_api_request):
        """Test generating dialogue with style adaptation."""
        # Mock the get_dialogue_style method
        self.analyzer.get_dialogue_style = MagicMock(return_value={
            "formality_level": 4,
            "verbosity_level": 3,
            "empathy_level": 5,
            "humor_level": 2
        })
        
        # Mock the get_conversation_history method
        self.analyzer.get_conversation_history = MagicMock(return_value=[
            {"id": 1, "content": "Hello", "role": "user"},
            {"id": 2, "content": "Hi there!", "role": "assistant"}
        ])
        
        # Mock the store_message method
        self.analyzer.store_message = MagicMock(return_value=3)
        
        # Mock the API response
        mock_make_api_request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "It's nice to meet you!"
                    }
                }
            ]
        }
        
        # Call the method
        dialogue, context_id = self.analyzer.generate_dialogue_with_style(
            user_id=1,
            prompt="Tell me about yourself",
            context_id="ctx_1"
        )
        
        # Check that get_dialogue_style was called
        self.analyzer.get_dialogue_style.assert_called_once_with(1)
        
        # Check that get_conversation_history was called
        self.analyzer.get_conversation_history.assert_called_once_with(user_id=1, limit=10, context_id="ctx_1")
        
        # Check that make_api_request was called
        mock_make_api_request.assert_called_once()
        
        # Check that store_message was called twice (once for user, once for AI)
        self.assertEqual(self.analyzer.store_message.call_count, 2)
        
        # Check the return values
        self.assertEqual(dialogue, "It's nice to meet you!")
        self.assertEqual(context_id, "ctx_1")


if __name__ == '__main__':
    unittest.main()
