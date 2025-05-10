import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PySide6.QtCore import Qt, QEvent
from PySide6.QtTest import QTest
from kindness_companion_app.frontend.main_window import MainWindow
from kindness_companion_app.frontend.theme_manager import ThemeManager


class TestThemeManager:
    def test_theme_detection(self, app):
        """测试主题检测"""
        theme_manager = ThemeManager(app, None)
        theme = theme_manager.detect_system_theme()
        assert theme in ["light", "dark"]

    def test_theme_application(self, app):
        """测试主题应用"""
        theme_manager = ThemeManager(app, None)

        # 测试深色主题
        theme_manager.current_theme = "dark"
        theme_manager.apply_theme()
        assert "background-color: #2A2F3A" in app.styleSheet()

        # 测试浅色主题
        theme_manager.current_theme = "light"
        theme_manager.apply_theme()
        assert "background-color: #F7F5F2" in app.styleSheet()

    def test_theme_style_switching(self, app):
        """测试主题样式切换"""
        theme_manager = ThemeManager(app, None)

        # 测试不同主题样式
        styles = ["standard", "warm", "sourcio"]
        for style in styles:
            theme_manager.theme_style = style
            theme_manager.apply_theme()
            # 验证样式表是否包含特定样式特征
            if style == "warm":
                assert "#2D2A3E" in app.styleSheet()
            elif style == "sourcio":
                assert "#F7F5F2" in app.styleSheet()
            else:  # standard
                assert "#333" in app.styleSheet()


class TestMainWindow:
    def test_window_initialization(
        self, app, user_manager, challenge_manager, progress_tracker, reminder_scheduler
    ):
        """测试主窗口初始化"""
        window = MainWindow(
            user_manager=user_manager,
            challenge_manager=challenge_manager,
            progress_tracker=progress_tracker,
            reminder_scheduler=reminder_scheduler,
        )
        assert window is not None
        assert window.windowTitle() == "Kindness Companion"
        window.close()

    def test_theme_switching(
        self, app, user_manager, challenge_manager, progress_tracker, reminder_scheduler
    ):
        """测试主题切换功能"""
        window = MainWindow(
            user_manager=user_manager,
            challenge_manager=challenge_manager,
            progress_tracker=progress_tracker,
            reminder_scheduler=reminder_scheduler,
        )

        # 获取主题切换按钮
        theme_button = window.findChild(QPushButton, "themeToggleButton")
        assert theme_button is not None

        # 模拟点击主题切换按钮
        initial_theme = window.theme_manager.current_theme
        QTest.mouseClick(theme_button, Qt.LeftButton)
        assert window.theme_manager.current_theme != initial_theme

        window.close()

    def test_challenge_creation(
        self, app, user_manager, challenge_manager, progress_tracker, reminder_scheduler
    ):
        """测试挑战创建功能"""
        window = MainWindow(
            user_manager=user_manager,
            challenge_manager=challenge_manager,
            progress_tracker=progress_tracker,
            reminder_scheduler=reminder_scheduler,
        )

        # 获取挑战创建按钮
        create_button = window.findChild(QPushButton, "createChallengeButton")
        assert create_button is not None

        # 模拟点击创建按钮
        QTest.mouseClick(create_button, Qt.LeftButton)

        # 验证挑战创建对话框是否显示
        dialog = window.findChild(QWidget, "createChallengeDialog")
        assert dialog is not None
        assert dialog.isVisible()

        window.close()

    def test_progress_tracking(
        self, app, user_manager, challenge_manager, progress_tracker, reminder_scheduler
    ):
        """测试进度追踪功能"""
        window = MainWindow(
            user_manager=user_manager,
            challenge_manager=challenge_manager,
            progress_tracker=progress_tracker,
            reminder_scheduler=reminder_scheduler,
        )

        # 获取进度更新按钮
        update_button = window.findChild(QPushButton, "updateProgressButton")
        assert update_button is not None

        # 模拟点击更新按钮
        QTest.mouseClick(update_button, Qt.LeftButton)

        # 验证进度更新对话框是否显示
        dialog = window.findChild(QWidget, "updateProgressDialog")
        assert dialog is not None
        assert dialog.isVisible()

        window.close()

    def test_reminder_settings(
        self, app, user_manager, challenge_manager, progress_tracker, reminder_scheduler
    ):
        """测试提醒设置功能"""
        window = MainWindow(
            user_manager=user_manager,
            challenge_manager=challenge_manager,
            progress_tracker=progress_tracker,
            reminder_scheduler=reminder_scheduler,
        )

        # 获取提醒设置按钮
        reminder_button = window.findChild(QPushButton, "reminderSettingsButton")
        assert reminder_button is not None

        # 模拟点击提醒设置按钮
        QTest.mouseClick(reminder_button, Qt.LeftButton)

        # 验证提醒设置对话框是否显示
        dialog = window.findChild(QWidget, "reminderSettingsDialog")
        assert dialog is not None
        assert dialog.isVisible()

        window.close()
