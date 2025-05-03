import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.report_generator import generate_weekly_report, _get_user_data_for_report, _call_text_generation_api

class TestReportGenerator(unittest.TestCase):
    """Test cases for the report_generator module."""

    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to avoid polluting test output
        logging.basicConfig(level=logging.CRITICAL)
        
        # Sample user data for testing
        self.sample_user_data = {
            "check_ins": 5,
            "streak": 3,
            "reflections": 2,
            "top_category": "社区服务",
            "new_achievements": ["善意新手"]
        }
        
        # Sample API response
        self.sample_api_response = "本周您完成了5次打卡，连续打卡3天，真是太棒了！您在社区服务方面表现突出，继续保持这种善意的行动吧！"

    @patch('ai_core.report_generator._get_user_data_for_report')
    @patch('ai_core.report_generator._call_text_generation_api')
    def test_generate_weekly_report_success(self, mock_call_api, mock_get_data):
        """Test successful report generation."""
        # Configure mocks
        mock_get_data.return_value = self.sample_user_data
        mock_call_api.return_value = self.sample_api_response
        
        # Call the function
        result = generate_weekly_report(1)
        
        # Verify the result
        self.assertEqual(result, self.sample_api_response)
        
        # Verify the mocks were called correctly
        mock_get_data.assert_called_once_with(1)
        mock_call_api.assert_called_once()  # We don't check the exact prompt as it may change
    
    @patch('ai_core.report_generator._get_user_data_for_report')
    def test_generate_weekly_report_no_data(self, mock_get_data):
        """Test report generation when no user data is available."""
        # Configure mock to return None (no data)
        mock_get_data.return_value = None
        
        # Call the function
        result = generate_weekly_report(1)
        
        # Verify the result is an error message
        self.assertTrue("无法生成报告" in result)
        
        # Verify the mock was called correctly
        mock_get_data.assert_called_once_with(1)
    
    @patch('ai_core.report_generator._get_user_data_for_report')
    @patch('ai_core.report_generator._call_text_generation_api')
    def test_generate_weekly_report_api_error(self, mock_call_api, mock_get_data):
        """Test report generation when the API call fails."""
        # Configure mocks
        mock_get_data.return_value = self.sample_user_data
        mock_call_api.return_value = None  # API call failed
        
        # Call the function
        result = generate_weekly_report(1)
        
        # Verify the result is an error message
        self.assertTrue("AI 正在思考中" in result)
        
        # Verify the mocks were called correctly
        mock_get_data.assert_called_once_with(1)
        mock_call_api.assert_called_once()
    
    @patch('backend.database_manager.DatabaseManager')
    @patch('backend.progress_tracker.ProgressTracker')
    @patch('backend.challenge_manager.ChallengeManager')
    def test_get_user_data_for_report(self, mock_challenge_manager, mock_progress_tracker, mock_db_manager):
        """Test fetching user data for the report."""
        # This test requires more complex mocking of the database and trackers
        # For simplicity, we'll just verify the function doesn't crash
        
        # Configure the mocks
        mock_progress_tracker_instance = MagicMock()
        mock_progress_tracker.return_value = mock_progress_tracker_instance
        
        # Mock check-ins data
        mock_progress_tracker_instance.get_all_user_check_ins.return_value = [
            {"challenge_id": 1, "notes": "Great experience!"},
            {"challenge_id": 2, "notes": ""}
        ]
        mock_progress_tracker_instance.get_total_check_ins.return_value = 10
        mock_progress_tracker_instance.get_longest_streak_all_challenges.return_value = 5
        
        # Mock challenge manager
        mock_challenge_manager_instance = MagicMock()
        mock_challenge_manager.return_value = mock_challenge_manager_instance
        mock_challenge_manager_instance.get_challenge_by_id.side_effect = lambda id: {
            1: {"category": "环保"},
            2: {"category": "社区服务"}
        }.get(id, None)
        
        # Call the function
        result = _get_user_data_for_report(1)
        
        # Verify the result has the expected structure
        self.assertIsInstance(result, dict)
        self.assertIn("check_ins", result)
        self.assertIn("streak", result)
        self.assertIn("reflections", result)
        self.assertIn("top_category", result)
        self.assertIn("new_achievements", result)
    
    @patch('ai_core.report_generator.get_api_key')
    @patch('ai_core.report_generator.make_api_request')
    def test_call_text_generation_api(self, mock_make_request, mock_get_api_key):
        """Test calling the text generation API."""
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
        result = _call_text_generation_api("Test prompt")
        
        # Verify the result
        self.assertEqual(result, "This is a test response")
        
        # Verify the mocks were called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')
        mock_make_request.assert_called_once()
    
    @patch('ai_core.report_generator.get_api_key')
    def test_call_text_generation_api_no_api_key(self, mock_get_api_key):
        """Test API call when no API key is available."""
        # Configure mock to return None (no API key)
        mock_get_api_key.return_value = None
        
        # Call the function
        result = _call_text_generation_api("Test prompt")
        
        # Verify the result is None
        self.assertIsNone(result)
        
        # Verify the mock was called correctly
        mock_get_api_key.assert_called_once_with('ZHIPUAI')

if __name__ == '__main__':
    unittest.main()
