import unittest
import os
import sys
from unittest.mock import MagicMock, patch
import datetime

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.progress_tracker import ProgressTracker
from backend.database_manager import DatabaseManager
from backend.challenge_manager import ChallengeManager


class TestProgressTracker(unittest.TestCase):
    """Test cases for the ProgressTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_challenge_manager = MagicMock(spec=ChallengeManager)
        self.progress_tracker = ProgressTracker(self.mock_db_manager)
        self.progress_tracker.challenge_manager = self.mock_challenge_manager

        # Sample data for tests
        self.sample_user_id = 1
        self.sample_challenge_id = 1
        self.sample_date = datetime.datetime.now().date().isoformat()
        self.sample_notes = "Test check-in notes"

    def test_check_in_success(self):
        """Test successful check-in with all parameters."""
        # Configure mock to return success
        self.mock_db_manager.execute_insert.return_value = 1

        # Perform check-in
        result = self.progress_tracker.check_in(
            self.sample_user_id,
            self.sample_challenge_id,
            self.sample_date,
            self.sample_notes,
        )

        # Verify result
        self.assertTrue(result)
        self.mock_db_manager.execute_insert.assert_called_once()

    def test_check_in_minimal(self):
        """Test check-in with minimal required parameters."""
        # Configure mock to return success
        self.mock_db_manager.execute_insert.return_value = 1

        # Perform check-in without notes
        result = self.progress_tracker.check_in(
            self.sample_user_id, self.sample_challenge_id, self.sample_date
        )

        # Verify result
        self.assertTrue(result)
        self.mock_db_manager.execute_insert.assert_called_once()

    def test_check_in_duplicate(self):
        """Test duplicate check-in handling."""
        # Configure mock to raise exception (simulating duplicate)
        self.mock_db_manager.execute_insert.side_effect = Exception("Duplicate entry")

        # Perform check-in
        result = self.progress_tracker.check_in(
            self.sample_user_id, self.sample_challenge_id, self.sample_date
        )

        # Verify result
        self.assertFalse(result)

    def test_check_in_database_error(self):
        """Test check-in with database error."""
        # Configure mock to raise general database error
        self.mock_db_manager.execute_insert.side_effect = Exception("Database error")

        # Perform check-in
        result = self.progress_tracker.check_in(
            self.sample_user_id, self.sample_challenge_id, self.sample_date
        )

        # Verify result
        self.assertFalse(result)

    def test_undo_check_in_success(self):
        """测试成功撤销打卡"""
        # 配置数据库返回值
        self.mock_db_manager.execute_update.return_value = 1

        # 撤销打卡
        result = self.progress_tracker.undo_check_in(1, 1)

        # 验证结果
        self.assertTrue(result)
        self.mock_db_manager.execute_update.assert_called_once()

    def test_undo_check_in_nonexistent(self):
        """测试撤销不存在的打卡"""
        # 配置数据库返回值
        self.mock_db_manager.execute_update.return_value = 0

        # 撤销打卡
        result = self.progress_tracker.undo_check_in(1, 1)

        # 验证结果
        self.assertFalse(result)
        self.mock_db_manager.execute_update.assert_called_once()

    def test_undo_check_in_database_error(self):
        """测试数据库错误时的打卡撤销"""
        # 配置数据库错误
        self.mock_db_manager.execute_update.side_effect = Exception("Database error")

        # 撤销打卡
        result = self.progress_tracker.undo_check_in(1, 1)

        # 验证结果
        self.assertFalse(result)  # 应该返回 False 而不是抛出异常
        self.mock_db_manager.execute_update.assert_called_once()

    def test_get_check_ins_success(self):
        """Test getting check-ins for a specific challenge."""
        # Sample progress data
        sample_progress = [
            {
                "id": 1,
                "user_id": self.sample_user_id,
                "challenge_id": self.sample_challenge_id,
                "check_in_date": self.sample_date,
                "notes": self.sample_notes,
            }
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_progress

        # Get check-ins
        result = self.progress_tracker.get_check_ins(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, sample_progress)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_check_ins_empty(self):
        """Test getting check-ins when none exist."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get check-ins
        result = self.progress_tracker.get_check_ins(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, [])
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_check_ins_database_error(self):
        """测试数据库错误时的打卡记录获取"""
        # 配置数据库错误
        self.mock_db_manager.execute_query.side_effect = Exception("Database error")

        # 获取打卡记录
        result = self.progress_tracker.get_check_ins(1, 1)

        # 验证结果
        self.assertEqual(result, [])  # 应该返回空列表而不是抛出异常
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_all_user_check_ins_success(self):
        """Test getting all check-ins for a user."""
        # Sample progress data
        sample_progress = [
            {
                "id": 1,
                "user_id": self.sample_user_id,
                "challenge_id": self.sample_challenge_id,
                "check_in_date": self.sample_date,
                "notes": self.sample_notes,
            }
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_progress

        # Get all user check-ins
        result = self.progress_tracker.get_all_user_check_ins(self.sample_user_id)

        # Verify result
        self.assertEqual(result, sample_progress)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_all_user_check_ins_empty(self):
        """Test getting all check-ins when none exist."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get all user check-ins
        result = self.progress_tracker.get_all_user_check_ins(self.sample_user_id)

        # Verify result
        self.assertEqual(result, [])
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_streak_consecutive(self):
        """Test getting streak with consecutive days."""
        # Sample progress data with consecutive days
        dates = [
            (datetime.datetime.now() - datetime.timedelta(days=i)).date().isoformat()
            for i in range(3)
        ]
        sample_progress = [
            {
                "id": i + 1,
                "user_id": self.sample_user_id,
                "challenge_id": self.sample_challenge_id,
                "check_in_date": date,
                "notes": f"Check-in {i+1}",
            }
            for i, date in enumerate(dates)
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_progress

        # Get streak
        result = self.progress_tracker.get_streak(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, 3)  # Should be 3 consecutive days
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_streak_with_gap(self):
        """Test getting streak with a gap in check-ins."""
        # Sample progress data with a gap
        dates = [
            datetime.datetime.now().date().isoformat(),
            (datetime.datetime.now() - datetime.timedelta(days=2)).date().isoformat(),
            (datetime.datetime.now() - datetime.timedelta(days=3)).date().isoformat(),
        ]
        sample_progress = [
            {
                "id": i + 1,
                "user_id": self.sample_user_id,
                "challenge_id": self.sample_challenge_id,
                "check_in_date": date,
                "notes": f"Check-in {i+1}",
            }
            for i, date in enumerate(dates)
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_progress

        # Get streak
        result = self.progress_tracker.get_streak(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, 1)  # Should be 1 due to gap
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_streak_empty(self):
        """Test getting streak with no check-ins."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get streak
        result = self.progress_tracker.get_streak(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, 0)  # Should be 0 with no check-ins
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_completion_rate_success(self):
        """Test getting completion rate with regular check-ins."""
        # Sample check-ins for the last 30 days
        today = datetime.datetime.now().date()
        dates = [
            (today - datetime.timedelta(days=i)).isoformat()
            for i in range(0, 30, 3)  # Check-ins every 3 days
        ]
        sample_progress = [
            {
                "id": i + 1,
                "user_id": self.sample_user_id,
                "challenge_id": self.sample_challenge_id,
                "check_in_date": date,
                "notes": f"Check-in {i+1}",
            }
            for i, date in enumerate(dates)
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_progress

        # Get completion rate
        result = self.progress_tracker.get_completion_rate(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result (10 check-ins in 30 days = 0.333...)
        self.assertAlmostEqual(result, 0.333, places=3)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_completion_rate_empty(self):
        """Test getting completion rate with no check-ins."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get completion rate
        result = self.progress_tracker.get_completion_rate(
            self.sample_user_id, self.sample_challenge_id
        )

        # Verify result
        self.assertEqual(result, 0.0)  # Should be 0 with no check-ins
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_check_ins_count_by_category_success(self):
        """Test getting check-in count by category."""
        # Configure mock to return count
        self.mock_db_manager.execute_query.return_value = [{"COUNT(p.id)": 5}]

        # Get count
        result = self.progress_tracker.get_check_ins_count_by_category(
            self.sample_user_id, "环保"
        )

        # Verify result
        self.assertEqual(result, 5)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_check_ins_count_by_category_empty(self):
        """Test getting check-in count by category with no check-ins."""
        # Configure mock to return zero count
        self.mock_db_manager.execute_query.return_value = [{"COUNT(p.id)": 0}]

        # Get count
        result = self.progress_tracker.get_check_ins_count_by_category(
            self.sample_user_id, "环保"
        )

        # Verify result
        self.assertEqual(result, 0)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_total_check_ins_success(self):
        """Test getting total check-ins for a user."""
        # Configure mock to return count
        self.mock_db_manager.execute_query.return_value = [{"total": 10}]

        # Get total
        result = self.progress_tracker.get_total_check_ins(self.sample_user_id)

        # Verify result
        self.assertEqual(result, 10)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_total_check_ins_empty(self):
        """Test getting total check-ins when none exist."""
        # Configure mock to return zero count
        self.mock_db_manager.execute_query.return_value = [{"total": 0}]

        # Get total
        result = self.progress_tracker.get_total_check_ins(self.sample_user_id)

        # Verify result
        self.assertEqual(result, 0)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_longest_streak_all_challenges_success(self):
        """测试获取所有挑战的最长连续打卡天数（聚合逻辑）"""
        self.mock_challenge_manager.get_user_challenges.return_value = [
            {"id": 1, "name": "Challenge 1"},
            {"id": 2, "name": "Challenge 2"},
        ]
        # 只关注聚合逻辑，mock get_streak
        with patch.object(
            self.progress_tracker, "get_streak", side_effect=[3, 2]
        ) as mock_get_streak:
            result = self.progress_tracker.get_longest_streak_all_challenges(1)
            self.assertEqual(result, 3)  # 应返回最大值 3
            self.mock_challenge_manager.get_user_challenges.assert_called_once_with(1)
            self.assertEqual(mock_get_streak.call_count, 2)

    def test_get_longest_streak_all_challenges_empty(self):
        """测试获取空挑战列表的最长连续打卡天数"""
        # 配置 mock 返回空列表
        self.mock_challenge_manager.get_user_challenges.return_value = []

        result = self.progress_tracker.get_longest_streak_all_challenges(1)
        self.assertEqual(result, 0)

        # 验证调用
        self.mock_challenge_manager.get_user_challenges.assert_called_once_with(1)
        self.mock_db_manager.execute_query.assert_not_called()

    def test_save_weekly_report_success(self):
        """Test saving a weekly report successfully."""
        # Sample report data
        report_text = "Weekly progress report"
        start_date = "2024-01-01"
        end_date = "2024-01-07"

        # Configure mock to return success
        self.mock_db_manager.execute_query.return_value = True

        # Save report
        result = self.progress_tracker.save_weekly_report(
            self.sample_user_id, report_text, start_date, end_date
        )

        # Verify result
        self.assertTrue(result)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_save_weekly_report_error(self):
        """Test saving a weekly report with database error."""
        # Sample report data
        report_text = "Weekly progress report"
        start_date = "2024-01-01"
        end_date = "2024-01-07"

        # Configure mock to raise exception
        self.mock_db_manager.execute_query.side_effect = Exception("Database error")

        # Save report
        result = self.progress_tracker.save_weekly_report(
            self.sample_user_id, report_text, start_date, end_date
        )

        # Verify result
        self.assertFalse(result)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_weekly_report_success(self):
        """Test getting a weekly report successfully."""
        # Sample report data
        sample_report = {
            "report_text": "Weekly progress report",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "created_at": "2024-01-07 12:00:00",
        }

        # Configure mock
        self.mock_db_manager.execute_query.return_value = [sample_report]

        # Get report
        result = self.progress_tracker.get_weekly_report(
            self.sample_user_id, "2024-01-01", "2024-01-07"
        )

        # Verify result
        self.assertEqual(result, sample_report)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_weekly_report_not_found(self):
        """Test getting a non-existent weekly report."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get report
        result = self.progress_tracker.get_weekly_report(
            self.sample_user_id, "2024-01-01", "2024-01-07"
        )

        # Verify result
        self.assertIsNone(result)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_all_weekly_reports_success(self):
        """Test getting all weekly reports successfully."""
        # Sample reports data
        sample_reports = [
            {
                "report_text": "Report 1",
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "created_at": "2024-01-07 12:00:00",
            },
            {
                "report_text": "Report 2",
                "start_date": "2024-01-08",
                "end_date": "2024-01-14",
                "created_at": "2024-01-14 12:00:00",
            },
        ]

        # Configure mock
        self.mock_db_manager.execute_query.return_value = sample_reports

        # Get all reports
        result = self.progress_tracker.get_all_weekly_reports(self.sample_user_id)

        # Verify result
        self.assertEqual(result, sample_reports)
        self.mock_db_manager.execute_query.assert_called_once()

    def test_get_all_weekly_reports_empty(self):
        """Test getting all weekly reports when none exist."""
        # Configure mock to return empty list
        self.mock_db_manager.execute_query.return_value = []

        # Get all reports
        result = self.progress_tracker.get_all_weekly_reports(self.sample_user_id)

        # Verify result
        self.assertEqual(result, [])
        self.mock_db_manager.execute_query.assert_called_once()


if __name__ == "__main__":
    unittest.main()
