import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.user_manager import UserManager
from kindness_companion_app.backend.challenge_manager import ChallengeManager
from kindness_companion_app.backend.progress_tracker import ProgressTracker
from kindness_companion_app.backend.reminder_scheduler import ReminderScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test")


@pytest.fixture(scope="session")
def app():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="session")
def db_manager():
    """创建数据库管理器实例"""
    manager = DatabaseManager()
    # 使用测试数据库
    manager.initialize_test_db()
    yield manager
    # 清理测试数据库
    manager.cleanup_test_db()


@pytest.fixture(scope="session")
def user_manager(db_manager):
    """创建用户管理器实例"""
    return UserManager(db_manager)


@pytest.fixture(scope="session")
def challenge_manager(db_manager):
    """创建挑战管理器实例"""
    return ChallengeManager(db_manager)


@pytest.fixture(scope="session")
def progress_tracker(db_manager):
    """创建进度追踪器实例"""
    return ProgressTracker(db_manager)


@pytest.fixture(scope="session")
def reminder_scheduler(db_manager):
    """创建提醒调度器实例"""
    return ReminderScheduler(db_manager)


@pytest.fixture(scope="function")
def test_user(user_manager):
    """创建测试用户"""
    user = user_manager.create_user("test_user", "test@example.com")
    yield user
    # 清理测试用户
    user_manager.delete_user(user.id)
