import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create a QApplication instance for the tests
app = QApplication.instance()
if not app:
    app = QApplication([])

from frontend.progress_ui import ProgressWidget
from backend.progress_tracker import ProgressTracker
from backend.challenge_manager import ChallengeManager

class TestProgressUI(unittest.TestCase):
    """Test cases for the ProgressWidget class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock backend components
        self.mock_progress_tracker = MagicMock(spec=ProgressTracker)
        self.mock_challenge_manager = MagicMock(spec=ChallengeManager)
        
        # Create a ProgressWidget instance with the mock components
        self.progress_widget = ProgressWidget(self.mock_progress_tracker, self.mock_challenge_manager)
        
        # Sample user data
        self.sample_user = {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "ai_consent_given": True
        }
        
        # Sample challenge data
        self.sample_challenges = [
            {
                "id": 1,
                "title": "每日微笑",
                "description": "对遇到的每个人微笑，传递善意",
                "category": "日常行为",
                "difficulty": 1
            },
            {
                "id": 2,
                "title": "扶老助残",
                "description": "帮助老人或残障人士完成一项任务",
                "category": "社区服务",
                "difficulty": 2
            }
        ]
        
        # Sample progress data
        self.sample_progress = [
            {
                "id": 1,
                "user_id": 1,
                "challenge_id": 1,
                "check_in_date": "2023-01-01",
                "notes": "Helped an elderly person cross the street"
            },
            {
                "id": 2,
                "user_id": 1,
                "challenge_id": 2,
                "check_in_date": "2023-01-02",
                "notes": "Volunteered at a local shelter"
            }
        ]
    
    def test_set_user(self):
        """Test setting the current user."""
        # Configure the mocks
        self.mock_challenge_manager.get_user_challenges.return_value = self.sample_challenges
        self.mock_progress_tracker.get_check_in_dates.return_value = ["2023-01-01", "2023-01-02"]
        self.mock_progress_tracker.get_total_check_ins.return_value = 2
        self.mock_progress_tracker.get_longest_streak_all_challenges.return_value = 2
        self.mock_progress_tracker.get_completion_rate_all_challenges.return_value = 50
        
        # Set the user
        self.progress_widget.set_user(self.sample_user)
        
        # Check that the user was set correctly
        self.assertEqual(self.progress_widget.current_user, self.sample_user)
        
        # Check that the mocks were called correctly
        self.mock_challenge_manager.get_user_challenges.assert_called_once_with(1)
        self.mock_progress_tracker.get_check_in_dates.assert_called_once_with(1)
        self.mock_progress_tracker.get_total_check_ins.assert_called_once_with(1)
        self.mock_progress_tracker.get_longest_streak_all_challenges.assert_called_once_with(1)
        self.mock_progress_tracker.get_completion_rate_all_challenges.assert_called_once_with(1)
    
    def test_set_user_none(self):
        """Test setting the current user to None."""
        # Set the user to None
        self.progress_widget.set_user(None)
        
        # Check that the user was cleared correctly
        self.assertIsNone(self.progress_widget.current_user)
        
        # Check that the progress was cleared
        self.assertEqual(self.progress_widget.challenge_combo.count(), 1)  # Only "All Challenges" item
        self.assertEqual(self.progress_widget.progress_table.rowCount(), 0)
        self.assertEqual(self.progress_widget.total_label.text(), "总打卡次数: 0")
        self.assertEqual(self.progress_widget.streak_label.text(), "当前连续打卡: 0 天")
        self.assertEqual(self.progress_widget.rate_label.text(), "完成率: 0%")
    
    def test_load_challenges(self):
        """Test loading challenges."""
        # Configure the mock
        self.mock_challenge_manager.get_user_challenges.return_value = self.sample_challenges
        
        # Set the user
        self.progress_widget.current_user = self.sample_user
        
        # Load challenges
        self.progress_widget.load_challenges()
        
        # Check that the challenges were loaded correctly
        self.assertEqual(self.progress_widget.challenge_combo.count(), 3)  # "All Challenges" + 2 challenges
        
        # Check that the mock was called correctly
        self.mock_challenge_manager.get_user_challenges.assert_called_once_with(1)
    
    def test_load_progress(self):
        """Test loading progress."""
        # Configure the mocks
        self.mock_progress_tracker.get_all_user_check_ins.return_value = self.sample_progress
        self.mock_challenge_manager.get_challenge_by_id.side_effect = lambda id: next((c for c in self.sample_challenges if c["id"] == id), None)
        
        # Set the user
        self.progress_widget.current_user = self.sample_user
        
        # Load progress
        self.progress_widget.load_progress()
        
        # Check that the progress was loaded correctly
        self.assertEqual(self.progress_widget.progress_table.rowCount(), 2)
        
        # Check that the mocks were called correctly
        self.mock_progress_tracker.get_all_user_check_ins.assert_called_once_with(1)
        self.assertEqual(self.mock_challenge_manager.get_challenge_by_id.call_count, 2)
    
    def test_update_stats(self):
        """Test updating stats."""
        # Configure the mocks
        self.mock_progress_tracker.get_total_check_ins.return_value = 2
        self.mock_progress_tracker.get_longest_streak_all_challenges.return_value = 2
        self.mock_progress_tracker.get_completion_rate_all_challenges.return_value = 50
        
        # Set the user
        self.progress_widget.current_user = self.sample_user
        
        # Update stats
        self.progress_widget.update_stats()
        
        # Check that the stats were updated correctly
        self.assertEqual(self.progress_widget.total_label.text(), "总打卡次数: 2")
        self.assertEqual(self.progress_widget.streak_label.text(), "当前连续打卡: 2 天")
        self.assertEqual(self.progress_widget.rate_label.text(), "完成率: 50%")
        
        # Check that the mocks were called correctly
        self.mock_progress_tracker.get_total_check_ins.assert_called_once_with(1)
        self.mock_progress_tracker.get_longest_streak_all_challenges.assert_called_once_with(1)
        self.mock_progress_tracker.get_completion_rate_all_challenges.assert_called_once_with(1)
    
    @patch('ai_core.report_generator.generate_weekly_report')
    def test_generate_weekly_report(self, mock_generate_report):
        """Test generating a weekly report."""
        # Configure the mock
        mock_generate_report.return_value = "This is a test report."
        
        # Set the user
        self.progress_widget.current_user = self.sample_user
        
        # Generate a report
        with patch('frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation') as mock_show_info:
            self.progress_widget.generate_weekly_report()
        
        # Check that the report was generated correctly
        self.assertEqual(self.progress_widget.weekly_report_text, "This is a test report.")
        
        # Check that the mock was called correctly
        mock_generate_report.assert_called_once_with(1)
        mock_show_info.assert_not_called()  # No message box should be shown for successful generation
    
    @patch('ai_core.report_generator.generate_weekly_report')
    def test_generate_weekly_report_no_consent(self, mock_generate_report):
        """Test generating a weekly report when the user has not given AI consent."""
        # Set the user with AI consent set to False
        user_without_consent = self.sample_user.copy()
        user_without_consent["ai_consent_given"] = False
        self.progress_widget.current_user = user_without_consent
        
        # Generate a report
        with patch('frontend.widgets.animated_message_box.AnimatedMessageBox.showInformation') as mock_show_info:
            self.progress_widget.generate_weekly_report()
        
        # Check that the report was not generated
        self.assertEqual(self.progress_widget.weekly_report_text, "")
        
        # Check that the mocks were called correctly
        mock_generate_report.assert_not_called()
        mock_show_info.assert_called_once()
    
    @patch('ai_core.report_generator.generate_weekly_report')
    def test_generate_weekly_report_error(self, mock_generate_report):
        """Test generating a weekly report when an error occurs."""
        # Configure the mock to raise an exception
        mock_generate_report.side_effect = Exception("Test error")
        
        # Set the user
        self.progress_widget.current_user = self.sample_user
        
        # Generate a report
        self.progress_widget.generate_weekly_report()
        
        # Check that the report text indicates an error
        self.assertTrue("生成报告时出错" in self.progress_widget.weekly_report_text_edit.toPlainText())
        
        # Check that the mock was called correctly
        mock_generate_report.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
