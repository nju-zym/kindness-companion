from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap

from .password_dialog import PasswordDialog


class ProfileWidget(QWidget):
    """
    Widget for displaying and editing user profile.
    """
    # Define signals
    user_updated = Signal(dict)
    user_logged_out = Signal()

    def __init__(self, user_manager, progress_tracker, challenge_manager):
        """
        Initialize the profile widget.

        Args:
            user_manager: User manager instance
            progress_tracker: Progress tracker instance
            challenge_manager: Challenge manager instance
        """
        super().__init__()

        self.user_manager = user_manager
        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        self.title_label = QLabel("个人信息")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.main_layout.addWidget(self.title_label)

        self.main_layout.addSpacing(20)

        # Content layout
        self.content_layout = QHBoxLayout()

        # Profile info
        self.setup_profile_info()
        self.content_layout.addWidget(self.profile_group)

        # Stats and achievements
        self.setup_stats()
        self.content_layout.addWidget(self.stats_group)

        self.main_layout.addLayout(self.content_layout)

    def setup_profile_info(self):
        """Set up the profile information section."""
        self.profile_group = QGroupBox("基本信息")
        self.profile_group.setMinimumWidth(300)
        self.profile_group.setMaximumWidth(400)

        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setContentsMargins(10, 15, 10, 15)  # 调整内边距

        # User info layout
        info_layout = QFormLayout()
        info_layout.setLabelAlignment(Qt.AlignRight)
        info_layout.setFormAlignment(Qt.AlignLeft)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(5, 5, 5, 5)  # 减小内边距

        # Username
        self.username_label = QLabel()
        info_layout.addRow("用户名:", self.username_label)

        profile_layout.addLayout(info_layout)

        profile_layout.addSpacing(25)  # 增加间距

        # 用简单的按钮替换原有的密码修改表单
        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setIcon(QIcon(":/icons/lock.svg"))
        self.change_password_button.setIconSize(QSize(16, 16))
        self.change_password_button.setMinimumHeight(40)
        self.change_password_button.clicked.connect(self.show_password_dialog)
        profile_layout.addWidget(self.change_password_button)

        profile_layout.addStretch(1)  # 添加弹性空间

        # Logout button
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")  # Set object name for styling
        self.logout_button.setIcon(QIcon(":/icons/log-out.svg"))
        self.logout_button.setIconSize(QSize(16, 16))
        self.logout_button.setMinimumHeight(40)
        self.logout_button.clicked.connect(self.logout)
        profile_layout.addWidget(self.logout_button)

    def setup_stats(self):
        """Set up the stats and achievements section."""
        self.stats_group = QGroupBox("统计与成就")

        stats_layout = QVBoxLayout(self.stats_group)

        # Summary layout
        summary_layout = QGridLayout()
        summary_layout.setSpacing(15)

        # Total check-ins
        self.total_label = QLabel("0")
        self.total_label.setAlignment(Qt.AlignCenter)

        total_title = QLabel("总打卡次数")
        total_title.setAlignment(Qt.AlignCenter)

        summary_layout.addWidget(self.total_label, 0, 0)
        summary_layout.addWidget(total_title, 1, 0)

        # Longest streak
        self.streak_label = QLabel("0")
        self.streak_label.setAlignment(Qt.AlignCenter)

        streak_title = QLabel("最长连续打卡")
        streak_title.setAlignment(Qt.AlignCenter)

        summary_layout.addWidget(self.streak_label, 0, 1)
        summary_layout.addWidget(streak_title, 1, 1)

        # Challenges
        self.challenges_label = QLabel("0")
        self.challenges_label.setAlignment(Qt.AlignCenter)

        challenges_title = QLabel("已订阅挑战")
        challenges_title.setAlignment(Qt.AlignCenter)

        summary_layout.addWidget(self.challenges_label, 0, 2)
        summary_layout.addWidget(challenges_title, 1, 2)

        stats_layout.addLayout(summary_layout)

        stats_layout.addSpacing(20)

        # Achievements
        achievements_group = QGroupBox("成就")
        achievements_layout = QVBoxLayout(achievements_group)

        # Beginner achievement
        beginner_layout = QHBoxLayout()
        beginner_title = QLabel("善行初学者")
        self.beginner_progress = QProgressBar()
        self.beginner_progress.setRange(0, 10)
        self.beginner_progress.setFormat("完成 %v/10 次打卡")

        beginner_layout.addWidget(beginner_title)
        beginner_layout.addWidget(self.beginner_progress)

        achievements_layout.addLayout(beginner_layout)

        # Consistent achievement
        consistent_layout = QHBoxLayout()
        consistent_title = QLabel("坚持不懈")
        self.consistent_progress = QProgressBar()
        self.consistent_progress.setRange(0, 7)
        self.consistent_progress.setFormat("连续打卡 %v/7 天")

        consistent_layout.addWidget(consistent_title)
        consistent_layout.addWidget(self.consistent_progress)

        achievements_layout.addLayout(consistent_layout)

        # Explorer achievement
        explorer_layout = QHBoxLayout()
        explorer_title = QLabel("善行探索者")
        self.explorer_progress = QProgressBar()
        self.explorer_progress.setRange(0, 5)
        self.explorer_progress.setFormat("订阅 %v/5 个挑战")

        explorer_layout.addWidget(explorer_title)
        explorer_layout.addWidget(self.explorer_progress)

        achievements_layout.addLayout(explorer_layout)

        # Master achievement
        master_layout = QHBoxLayout()
        master_title = QLabel("善行大师")
        self.master_progress = QProgressBar()
        self.master_progress.setRange(0, 30)
        self.master_progress.setFormat("完成 %v/30 次打卡")

        master_layout.addWidget(master_title)
        master_layout.addWidget(self.master_progress)

        achievements_layout.addLayout(master_layout)

        stats_layout.addWidget(achievements_group)

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information
        """
        self.current_user = user

        if user:
            # Update profile info
            self.username_label.setText(user["username"])

            # Load stats
            self.load_stats()
        else:
            # Clear profile info
            self.username_label.setText("")

            # Reset stats
            self.reset_stats()

    def load_stats(self):
        """Load and display user stats and achievements."""
        if not self.current_user:
            return

        # Get all user check-ins
        check_ins = self.progress_tracker.get_all_user_check_ins(self.current_user["id"])

        # Calculate total check-ins
        total_check_ins = len(check_ins)
        self.total_label.setText(str(total_check_ins))

        # Calculate longest streak
        # This is a simplified version that doesn't account for all challenges
        # In a real app, you would calculate the longest streak across all challenges
        longest_streak = 0

        # Get subscribed challenges
        challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])

        for challenge in challenges:
            streak = self.progress_tracker.get_streak(
                self.current_user["id"], challenge["id"]
            )
            longest_streak = max(longest_streak, streak)

        self.streak_label.setText(str(longest_streak))

        # Set subscribed challenges count
        self.challenges_label.setText(str(len(challenges)))

        # Update achievements
        self.beginner_progress.setValue(min(total_check_ins, 10))
        self.consistent_progress.setValue(min(longest_streak, 7))
        self.explorer_progress.setValue(min(len(challenges), 5))
        self.master_progress.setValue(min(total_check_ins, 30))

    def reset_stats(self):
        """Reset stats and achievements."""
        self.total_label.setText("0")
        self.streak_label.setText("0")
        self.challenges_label.setText("0")

        self.beginner_progress.setValue(0)
        self.consistent_progress.setValue(0)
        self.explorer_progress.setValue(0)
        self.master_progress.setValue(0)

    def show_password_dialog(self):
        """Show the password change dialog."""
        if not self.current_user:
            return

        dialog = PasswordDialog(self.user_manager, self.current_user, self)
        dialog.password_changed.connect(self.update_user_info)
        dialog.exec()

    def update_user_info(self, user_info):
        """
        Update user information in the application.

        Args:
            user_info (dict): Updated user information
        """
        self.current_user = user_info
        self.user_updated.emit(user_info)

    def logout(self):
        """Log out the current user."""
        reply = QMessageBox.question(
            self,
            "退出登录",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_user = None
            self.reset_stats()
            # Emit signal slightly delayed after confirmation
            QTimer.singleShot(10, self.user_logged_out.emit)
