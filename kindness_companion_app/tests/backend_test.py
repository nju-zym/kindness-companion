import pytest
from datetime import datetime, timedelta
from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.user_manager import UserManager
from kindness_companion_app.backend.challenge_manager import ChallengeManager
from kindness_companion_app.backend.progress_tracker import ProgressTracker
from kindness_companion_app.backend.reminder_scheduler import ReminderScheduler


class TestDatabaseManager:
    def test_initialize_test_db(self, db_manager):
        """测试测试数据库初始化"""
        assert db_manager.is_connected()
        # 验证必要的表是否创建
        tables = db_manager.get_all_tables()
        assert "users" in tables
        assert "challenges" in tables
        assert "progress" in tables
        assert "reminders" in tables

    def test_cleanup_test_db(self, db_manager):
        """测试测试数据库清理"""
        db_manager.cleanup_test_db()
        assert not db_manager.is_connected()


class TestUserManager:
    def test_create_user(self, user_manager):
        """测试用户创建"""
        user = user_manager.create_user("test_user2", "test2@example.com")
        assert user is not None
        assert user.username == "test_user2"
        assert user.email == "test2@example.com"
        # 清理
        user_manager.delete_user(user.id)

    def test_get_user(self, user_manager, test_user):
        """测试获取用户"""
        user = user_manager.get_user(test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    def test_update_user(self, user_manager, test_user):
        """测试更新用户信息"""
        new_username = "updated_user"
        user_manager.update_user(test_user.id, username=new_username)
        updated_user = user_manager.get_user(test_user.id)
        assert updated_user.username == new_username


class TestChallengeManager:
    def test_create_challenge(self, challenge_manager, test_user):
        """测试创建挑战"""
        challenge = challenge_manager.create_challenge(
            title="Test Challenge",
            description="Test Description",
            difficulty="easy",
            duration_days=7,
            user_id=test_user.id,
        )
        assert challenge is not None
        assert challenge.title == "Test Challenge"
        assert challenge.difficulty == "easy"
        # 清理
        challenge_manager.delete_challenge(challenge.id)

    def test_get_user_challenges(self, challenge_manager, test_user):
        """测试获取用户的挑战列表"""
        # 创建测试挑战
        challenge = challenge_manager.create_challenge(
            title="Test Challenge",
            description="Test Description",
            difficulty="easy",
            duration_days=7,
            user_id=test_user.id,
        )
        challenges = challenge_manager.get_user_challenges(test_user.id)
        assert len(challenges) > 0
        assert any(c.id == challenge.id for c in challenges)
        # 清理
        challenge_manager.delete_challenge(challenge.id)


class TestProgressTracker:
    def test_track_progress(self, progress_tracker, test_user):
        """测试进度追踪"""
        # 创建测试挑战
        challenge_manager = ChallengeManager(progress_tracker.db_manager)
        challenge = challenge_manager.create_challenge(
            title="Test Challenge",
            description="Test Description",
            difficulty="easy",
            duration_days=7,
            user_id=test_user.id,
        )

        # 记录进度
        progress = progress_tracker.record_progress(
            user_id=test_user.id,
            challenge_id=challenge.id,
            status="completed",
            notes="Test completion",
        )
        assert progress is not None
        assert progress.status == "completed"

        # 获取进度历史
        history = progress_tracker.get_progress_history(test_user.id, challenge.id)
        assert len(history) > 0
        assert any(p.id == progress.id for p in history)

        # 清理
        challenge_manager.delete_challenge(challenge.id)


class TestReminderScheduler:
    def test_schedule_reminder(self, reminder_scheduler, test_user):
        """测试提醒调度"""
        # 创建测试挑战
        challenge_manager = ChallengeManager(reminder_scheduler.db_manager)
        challenge = challenge_manager.create_challenge(
            title="Test Challenge",
            description="Test Description",
            difficulty="easy",
            duration_days=7,
            user_id=test_user.id,
        )

        # 设置提醒
        reminder_time = datetime.now() + timedelta(days=1)
        reminder = reminder_scheduler.schedule_reminder(
            user_id=test_user.id,
            challenge_id=challenge.id,
            reminder_time=reminder_time,
            message="Test reminder",
        )
        assert reminder is not None
        assert reminder.message == "Test reminder"

        # 获取待处理提醒
        pending = reminder_scheduler.get_pending_reminders(test_user.id)
        assert len(pending) > 0
        assert any(r.id == reminder.id for r in pending)

        # 清理
        challenge_manager.delete_challenge(challenge.id)
