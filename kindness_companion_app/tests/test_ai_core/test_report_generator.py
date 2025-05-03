import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.report_generator import (
    generate_weekly_report,
    _get_user_data_for_report,
    _call_text_generation_api,
    _build_report_prompt,
    _post_process_report,
    _get_additional_context
)

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
    @patch('ai_core.report_generator._get_additional_context')
    @patch('ai_core.report_generator._call_text_generation_api')
    @patch('ai_core.report_generator._post_process_report')
    def test_generate_weekly_report_success(self, mock_post_process, mock_call_api, mock_get_additional, mock_get_data):
        """Test successful report generation."""
        # Configure mocks
        mock_get_data.return_value = self.sample_user_data
        mock_get_additional.return_value = {"total_challenges": 3, "completion_rate": 0.7}
        mock_call_api.return_value = "Raw API response"
        mock_post_process.return_value = self.sample_api_response

        # Call the function
        result = generate_weekly_report(1)

        # Verify the result
        self.assertEqual(result, self.sample_api_response)

        # Verify the mocks were called correctly
        mock_get_data.assert_called_once_with(1)
        mock_get_additional.assert_called_once_with(1, self.sample_user_data)
        mock_call_api.assert_called_once()  # We don't check the exact prompt as it may change
        mock_post_process.assert_called_once_with("Raw API response")

    @patch('ai_core.report_generator._get_user_data_for_report')
    @patch('ai_core.report_generator._get_additional_context')
    def test_generate_weekly_report_no_data(self, mock_get_additional, mock_get_data):
        """Test report generation when no user data is available."""
        # Configure mock to return None (no data)
        mock_get_data.return_value = None
        # Additional context should not be called if there's no data
        mock_get_additional.return_value = {}

        # Call the function
        result = generate_weekly_report(1)

        # Verify the result is an error message
        self.assertTrue("无法生成报告" in result)

        # Verify the mock was called correctly
        mock_get_data.assert_called_once_with(1)
        # Additional context should not be called if there's no data
        mock_get_additional.assert_not_called()

    @patch('ai_core.report_generator._get_user_data_for_report')
    @patch('ai_core.report_generator._get_additional_context')
    @patch('ai_core.report_generator._call_text_generation_api')
    def test_generate_weekly_report_api_error(self, mock_call_api, mock_get_additional, mock_get_data):
        """Test report generation when the API call fails."""
        # Configure mocks
        mock_get_data.return_value = self.sample_user_data
        mock_get_additional.return_value = {"total_challenges": 3}
        mock_call_api.return_value = None  # API call failed

        # Call the function
        result = generate_weekly_report(1)

        # Verify the result is an error message
        self.assertTrue("AI 正在思考中" in result)

        # Verify the mocks were called correctly
        mock_get_data.assert_called_once_with(1)
        mock_get_additional.assert_called_once_with(1, self.sample_user_data)
        mock_call_api.assert_called_once()

    def test_post_process_report(self):
        """Test post-processing of report text."""
        # Test with a prefix that should be removed
        prefixed_text = "这是您的周报：您本周完成了5次打卡，真棒！"
        result = _post_process_report(prefixed_text)
        self.assertEqual(result, "您本周完成了5次打卡，真棒！")

        # Test with no prefix
        clean_text = "您本周完成了5次打卡，真棒！"
        result = _post_process_report(clean_text)
        self.assertEqual(result, clean_text)

    def test_build_report_prompt(self):
        """Test building the report prompt."""
        user_id = 1
        user_data = {
            "check_ins": 5,
            "streak": 3,
            "reflections": 2,
            "top_category": "社区服务",
            "new_achievements": ["善意新手"]
        }
        additional_context = {
            "total_challenges": 3,
            "completion_rate": 0.7,
            "previous_week_check_ins": 4
        }

        # Call the function
        prompt = _build_report_prompt(user_id, user_data, additional_context)

        # Verify the prompt contains the expected data
        self.assertIn("用户 ID: 1", prompt)
        self.assertIn("完成打卡次数: 5", prompt)
        self.assertIn("当前连胜天数: 3", prompt)
        self.assertIn("主要参与的挑战类别: 社区服务", prompt)
        self.assertIn("参与的总挑战数: 3", prompt)
        self.assertIn("本周完成率: 70.0%", prompt)

    @patch('backend.database_manager.DatabaseManager')
    @patch('backend.progress_tracker.ProgressTracker')
    @patch('backend.challenge_manager.ChallengeManager')
    def test_get_user_data_for_report(self, mock_challenge_manager, mock_progress_tracker, mock_db_manager_class):
        """Test fetching user data for the report."""
        # This test requires more complex mocking of the database and trackers
        # For simplicity, we'll just verify the function doesn't crash

        # Configure the mocks
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager

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

    @patch('backend.database_manager.DatabaseManager')
    @patch('backend.progress_tracker.ProgressTracker')
    @patch('backend.challenge_manager.ChallengeManager')
    def test_get_additional_context(self, mock_challenge_manager, mock_progress_tracker, mock_db_manager_class):
        """Test getting additional context for the report."""
        # Configure the mocks
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager

        mock_progress_tracker_instance = MagicMock()
        mock_progress_tracker.return_value = mock_progress_tracker_instance

        # Mock check-ins data for previous week
        mock_progress_tracker_instance.get_all_user_check_ins.return_value = [
            {"challenge_id": 1, "check_in_date": "2023-05-01"},
            {"challenge_id": 2, "check_in_date": "2023-05-02"}
        ]

        # Mock challenge manager
        mock_challenge_manager_instance = MagicMock()
        mock_challenge_manager.return_value = mock_challenge_manager_instance
        mock_challenge_manager_instance.get_user_challenges.return_value = [
            {"id": 1, "title": "Challenge 1"},
            {"id": 2, "title": "Challenge 2"},
            {"id": 3, "title": "Challenge 3"}
        ]

        # Current data for the user
        current_data = {
            "check_ins": 5,
            "streak": 3
        }

        # Call the function
        result = _get_additional_context(1, current_data)

        # Verify the result has the expected structure
        self.assertIsInstance(result, dict)
        self.assertIn("previous_week_check_ins", result)
        self.assertIn("total_challenges", result)
        self.assertIn("completion_rate", result)

        # Verify the values
        self.assertEqual(result["previous_week_check_ins"], 2)
        self.assertEqual(result["total_challenges"], 3)

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
