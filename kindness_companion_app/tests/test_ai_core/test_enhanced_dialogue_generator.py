"""
Test module for the enhanced dialogue generator.
"""

import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kindness_companion_app.ai_core.enhanced_dialogue_generator import EnhancedDialogueGenerator
from kindness_companion_app.backend.database_manager import DatabaseManager


class TestEnhancedDialogueGenerator(unittest.TestCase):
    """Test cases for the EnhancedDialogueGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock database manager
        self.db_manager = MagicMock(spec=DatabaseManager)
        
        # Create a mock conversation analyzer
        self.mock_conversation_analyzer = MagicMock()
        
        # Create an enhanced dialogue generator with the mock database manager
        with patch('kindness_companion_app.ai_core.enhanced_dialogue_generator.ConversationAnalyzer') as mock_analyzer_class:
            mock_analyzer_class.return_value = self.mock_conversation_analyzer
            self.generator = EnhancedDialogueGenerator(self.db_manager)
            
        # Sample event data
        self.sample_check_in_event = {
            "challenge_title": "每日微笑",
            "streak": 3
        }
        
        self.sample_reflection_event = {
            "text": "今天帮助了一位老人过马路，感觉很开心。",
            "analyzed_emotion": "positive"
        }
        
        self.sample_user_message_event = {
            "message": "你好，今天天气真好！",
            "analyzed_emotion": "positive"
        }
        
        # Sample dialogue response
        self.sample_dialogue_response = {
            "dialogue": "你好！今天确实是个好天气，很高兴你心情不错！",
            "context_id": "ctx_123",
            "profile_available": True
        }

    def test_generate_dialogue_check_in(self):
        """Test generating dialogue for a check-in event."""
        # Mock the conversation_analyzer.generate_dialogue_with_style method
        self.mock_conversation_analyzer.generate_dialogue_with_style.return_value = (
            self.sample_dialogue_response["dialogue"],
            self.sample_dialogue_response["context_id"]
        )
        
        # Mock the conversation_analyzer.get_psychological_profile method
        self.mock_conversation_analyzer.get_psychological_profile.return_value = {
            "personality_traits": {"extraversion": "high"}
        }
        
        # Call the method
        response = self.generator.generate_dialogue(
            user_id=1,
            event_type="check_in",
            event_data=self.sample_check_in_event
        )
        
        # Check that generate_dialogue_with_style was called with the correct parameters
        self.mock_conversation_analyzer.generate_dialogue_with_style.assert_called_once()
        args, kwargs = self.mock_conversation_analyzer.generate_dialogue_with_style.call_args
        self.assertEqual(args[0], 1)  # user_id
        self.assertIn("他们刚刚为挑战"每日微笑"打卡", args[1])  # prompt
        self.assertIn("这是他们连续第3天完成这个挑战", args[1])  # prompt
        
        # Check the return value
        self.assertEqual(response["dialogue"], self.sample_dialogue_response["dialogue"])
        self.assertEqual(response["context_id"], self.sample_dialogue_response["context_id"])
        self.assertEqual(response["profile_available"], True)

    def test_generate_dialogue_reflection(self):
        """Test generating dialogue for a reflection event."""
        # Mock the conversation_analyzer.generate_dialogue_with_style method
        self.mock_conversation_analyzer.generate_dialogue_with_style.return_value = (
            self.sample_dialogue_response["dialogue"],
            self.sample_dialogue_response["context_id"]
        )
        
        # Mock the conversation_analyzer.get_psychological_profile method
        self.mock_conversation_analyzer.get_psychological_profile.return_value = {
            "personality_traits": {"extraversion": "high"}
        }
        
        # Call the method
        response = self.generator.generate_dialogue(
            user_id=1,
            event_type="reflection_added",
            event_data=self.sample_reflection_event
        )
        
        # Check that generate_dialogue_with_style was called with the correct parameters
        self.mock_conversation_analyzer.generate_dialogue_with_style.assert_called_once()
        args, kwargs = self.mock_conversation_analyzer.generate_dialogue_with_style.call_args
        self.assertEqual(args[0], 1)  # user_id
        self.assertIn("他们添加了一条反思", args[1])  # prompt
        
        # Check the return value
        self.assertEqual(response["dialogue"], self.sample_dialogue_response["dialogue"])
        self.assertEqual(response["context_id"], self.sample_dialogue_response["context_id"])
        self.assertEqual(response["profile_available"], True)

    def test_generate_dialogue_user_message(self):
        """Test generating dialogue for a user message event."""
        # Mock the conversation_analyzer.generate_dialogue_with_style method
        self.mock_conversation_analyzer.generate_dialogue_with_style.return_value = (
            self.sample_dialogue_response["dialogue"],
            self.sample_dialogue_response["context_id"]
        )
        
        # Mock the conversation_analyzer.get_psychological_profile method
        self.mock_conversation_analyzer.get_psychological_profile.return_value = {
            "personality_traits": {"extraversion": "high"}
        }
        
        # Mock the conversation_analyzer.store_message method
        self.mock_conversation_analyzer.store_message.return_value = 1
        
        # Call the method
        response = self.generator.generate_dialogue(
            user_id=1,
            event_type="user_message",
            event_data=self.sample_user_message_event
        )
        
        # Check that store_message was called for the user message
        self.mock_conversation_analyzer.store_message.assert_called_once()
        args, kwargs = self.mock_conversation_analyzer.store_message.call_args
        self.assertEqual(args[0], 1)  # user_id
        self.assertEqual(args[1], "你好，今天天气真好！")  # message
        self.assertEqual(args[2], True)  # is_user
        
        # Check that generate_dialogue_with_style was called with the correct parameters
        self.mock_conversation_analyzer.generate_dialogue_with_style.assert_called_once()
        args, kwargs = self.mock_conversation_analyzer.generate_dialogue_with_style.call_args
        self.assertEqual(args[0], 1)  # user_id
        self.assertIn("用户向你发送了一条消息", args[1])  # prompt
        
        # Check the return value
        self.assertEqual(response["dialogue"], self.sample_dialogue_response["dialogue"])
        self.assertEqual(response["context_id"], self.sample_dialogue_response["context_id"])
        self.assertEqual(response["profile_available"], True)

    def test_suggest_animation(self):
        """Test suggesting animation based on event and profile."""
        # Test with check-in event
        animation = self.generator._suggest_animation(
            event_type="check_in",
            event_data={},
            profile=None
        )
        self.assertEqual(animation, "happy")
        
        # Test with user message and positive emotion
        animation = self.generator._suggest_animation(
            event_type="user_message",
            event_data={"analyzed_emotion": "positive"},
            profile=None
        )
        self.assertEqual(animation, "excited")
        
        # Test with user message and negative emotion
        animation = self.generator._suggest_animation(
            event_type="user_message",
            event_data={"analyzed_emotion": "negative"},
            profile=None
        )
        self.assertEqual(animation, "concerned")
        
        # Test with profile adjustment (serious user)
        animation = self.generator._suggest_animation(
            event_type="user_message",
            event_data={"analyzed_emotion": "positive"},
            profile={"personality_traits": {"seriousness": "high"}}
        )
        self.assertEqual(animation, "happy")  # Toned down from excited to happy

    def test_reset_context(self):
        """Test resetting conversation context."""
        # Set up an active context
        self.generator.active_contexts[1] = "ctx_123"
        
        # Reset the context
        self.generator.reset_context(user_id=1)
        
        # Check that the context was removed
        self.assertNotIn(1, self.generator.active_contexts)

    def test_get_active_context(self):
        """Test getting active conversation context."""
        # Set up an active context
        self.generator.active_contexts[1] = "ctx_123"
        
        # Get the context
        context_id = self.generator.get_active_context(user_id=1)
        
        # Check the return value
        self.assertEqual(context_id, "ctx_123")
        
        # Test with non-existent user
        context_id = self.generator.get_active_context(user_id=2)
        self.assertIsNone(context_id)


if __name__ == '__main__':
    unittest.main()
