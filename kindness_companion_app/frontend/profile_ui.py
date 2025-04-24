from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy, QTextEdit # 添加 QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox
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
        # ... (初始化保持不变)
        super().__init__()

        self.user_manager = user_manager
        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user = None

        # 初始化新 UI 元素
        self.avatar_label = None
        self.username_label = None
        self.reg_date_label = None
        self.bio_display_label = None
        self.bio_edit = None
        self.edit_bio_button = None
        self.save_bio_button = None
        self.cancel_bio_button = None

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
        # Add stats_group with a stretch factor of 1 to allow horizontal expansion
        self.content_layout.addWidget(self.stats_group, 1)

        self.main_layout.addLayout(self.content_layout)

    def setup_profile_info(self):
        """Set up the profile information section."""
        self.profile_group = QGroupBox("基本信息")
        self.profile_group.setMinimumWidth(350) # 稍微加宽以容纳更多信息
        self.profile_group.setMaximumWidth(450)

        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setContentsMargins(15, 20, 15, 20) # 调整内边距
        profile_layout.setSpacing(15) # 设置元素间距

        # --- Avatar ---
        avatar_layout = QHBoxLayout()
        avatar_layout.setAlignment(Qt.AlignCenter)
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatar_label") # <--- Add object name
        # 设置一个默认/占位头像
        default_avatar_path = ":/images/profilePicture.png" # Use profilePicture.png
        pixmap = QPixmap(default_avatar_path)
        self.avatar_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.avatar_label.setFixedSize(80, 80)
        # self.avatar_label.setStyleSheet("border: 1px solid #ccc; border-radius: 40px;") # <--- Remove this line
        # 可以添加一个按钮来更改头像 (未来功能)
        # change_avatar_button = QPushButton("更换头像")
        # change_avatar_button.clicked.connect(self.change_avatar) # 需要实现 change_avatar
        avatar_layout.addWidget(self.avatar_label)
        # avatar_layout.addWidget(change_avatar_button)
        profile_layout.addLayout(avatar_layout)

        # --- User Info ---
        info_layout = QFormLayout()
        info_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(5, 15, 5, 5)

        # Username
        self.username_label = QLabel("N/A")
        info_layout.addRow("用户名:", self.username_label)

        # Registration Date
        self.reg_date_label = QLabel("N/A") # 注册日期标签
        info_layout.addRow("注册日期:", self.reg_date_label)

        profile_layout.addLayout(info_layout)

        # --- Bio Section ---
        bio_group = QGroupBox("个人简介")
        bio_layout = QVBoxLayout(bio_group)
        bio_layout.setSpacing(5)

        self.bio_display_label = QLabel("这个人很神秘，什么也没留下...")
        self.bio_display_label.setWordWrap(True)
        self.bio_display_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.bio_display_label.setMinimumHeight(60) # 保证一定高度
        self.bio_display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.bio_edit = QTextEdit()
        self.bio_edit.setPlaceholderText("编辑您的个人简介...")
        self.bio_edit.setVisible(False) # 初始隐藏
        self.bio_edit.setMinimumHeight(60)
        self.bio_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        bio_button_layout = QHBoxLayout()
        bio_button_layout.addStretch(1)

        self.edit_bio_button = QPushButton("编辑")
        self.edit_bio_button.setIcon(QIcon(":/icons/edit-2.svg"))
        self.edit_bio_button.clicked.connect(self.toggle_bio_edit)

        self.save_bio_button = QPushButton("保存")
        self.save_bio_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_bio_button.setVisible(False) # 初始隐藏
        self.save_bio_button.clicked.connect(self.save_bio)

        self.cancel_bio_button = QPushButton("取消")
        self.cancel_bio_button.setVisible(False) # 初始隐藏
        self.cancel_bio_button.clicked.connect(self.toggle_bio_edit) # 取消也切换状态

        bio_button_layout.addWidget(self.edit_bio_button)
        bio_button_layout.addWidget(self.save_bio_button)
        bio_button_layout.addWidget(self.cancel_bio_button)

        bio_layout.addWidget(self.bio_display_label)
        bio_layout.addWidget(self.bio_edit)
        bio_layout.addLayout(bio_button_layout)

        profile_layout.addWidget(bio_group)

        # --- Action Buttons ---
        action_button_layout = QVBoxLayout()
        action_button_layout.setSpacing(10) # 按钮间距

        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setIcon(QIcon(":/icons/lock.svg"))
        self.change_password_button.setIconSize(QSize(16, 16))
        self.change_password_button.setMinimumHeight(35) # 调整高度
        self.change_password_button.clicked.connect(self.show_password_dialog)
        action_button_layout.addWidget(self.change_password_button)

        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")
        self.logout_button.setIcon(QIcon(":/icons/log-out.svg"))
        self.logout_button.setIconSize(QSize(16, 16))
        self.logout_button.setMinimumHeight(35) # 调整高度
        self.logout_button.clicked.connect(self.logout)
        action_button_layout.addWidget(self.logout_button)

        profile_layout.addLayout(action_button_layout)

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
        """Set the current user and update UI elements."""
        self.current_user = user

        if user:
            # Update profile info
            self.username_label.setText(user.get("username", "N/A"))

            # --- Load Avatar (Placeholder/Example) ---
            # In a real app, load from user data (e.g., user.get("avatar_path"))
            avatar_path = user.get("avatar_path", ":/images/profilePicture.png") # Use profilePicture.png
            pixmap = QPixmap(avatar_path)
            if pixmap.isNull(): # Fallback if path is invalid
                pixmap = QPixmap(":/images/profilePicture.png") # Use profilePicture.png
            self.avatar_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # --- Load Registration Date (Placeholder/Example) ---
            # In a real app, load from user data and format it
            reg_date_str = user.get("registration_date", "未知") # Assume backend provides this
            # You might want to format the date:
            # from PySide6.QtCore import QDateTime
            # reg_dt = QDateTime.fromString(reg_date_str, Qt.ISODate)
            # if reg_dt.isValid():
            #     self.reg_date_label.setText(reg_dt.toString("yyyy-MM-dd"))
            # else:
            #     self.reg_date_label.setText("未知")
            self.reg_date_label.setText(reg_date_str if reg_date_str else "未知")


            # --- Load Bio ---
            bio = user.get("bio", "")
            if bio:
                self.bio_display_label.setText(bio)
                self.bio_edit.setText(bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")
                self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

            # Load stats
            self.load_stats()
        else:
            # Clear profile info
            self.username_label.setText("N/A")
            # Reset avatar to default
            default_pixmap = QPixmap(":/images/profilePicture.png") # Use profilePicture.png
            self.avatar_label.setPixmap(default_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # Reset reg date
            self.reg_date_label.setText("N/A")
            # Reset bio
            self.bio_display_label.setText("请先登录")
            self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

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
        """Reset stats and achievements, and clear profile fields on logout."""
        # Reset stats labels
        self.total_label.setText("0")
        self.streak_label.setText("0")
        self.challenges_label.setText("0")

        # Reset progress bars
        self.beginner_progress.setValue(0)
        self.consistent_progress.setValue(0)
        self.explorer_progress.setValue(0)
        self.master_progress.setValue(0)

        # Clear profile fields (already handled in set_user(None), but good practice)
        if self.username_label: self.username_label.setText("N/A")
        if self.avatar_label:
             default_pixmap = QPixmap(":/images/profilePicture.png") # Use profilePicture.png
             self.avatar_label.setPixmap(default_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if self.reg_date_label: self.reg_date_label.setText("N/A")
        if self.bio_display_label: self.bio_display_label.setText("请先登录")
        if self.bio_edit: self.bio_edit.setText("")
        self.toggle_bio_edit(edit_mode=False) # Ensure display mode

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
        # Ask for confirmation using AnimatedMessageBox
        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
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

    # --- Bio Editing Methods ---
    @Slot(bool)
    def toggle_bio_edit(self, edit_mode=None):
        """Toggle between displaying and editing the bio."""
        if edit_mode is None:
            # Toggle based on current visibility of edit button
            currently_editing = not self.edit_bio_button.isVisible()
            edit_mode = not currently_editing
        else:
            currently_editing = not edit_mode

        self.bio_display_label.setVisible(not edit_mode)
        self.edit_bio_button.setVisible(not edit_mode)

        self.bio_edit.setVisible(edit_mode)
        self.save_bio_button.setVisible(edit_mode)
        self.cancel_bio_button.setVisible(edit_mode)

        if not edit_mode: # If switching back to display mode
             # Reset edit text to current display text in case of cancel
             current_bio = self.bio_display_label.text()
             if current_bio == "这个人很神秘，什么也没留下..." or current_bio == "请先登录":
                 self.bio_edit.setText("")
             else:
                 self.bio_edit.setText(current_bio)

    @Slot()
    def save_bio(self):
        """Save the edited bio."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "用户未登录")
            return

        new_bio = self.bio_edit.toPlainText().strip()

        # --- Backend Call (Placeholder) ---
        # success = self.user_manager.update_profile(self.current_user["id"], bio=new_bio)
        # Simulating success for now
        success = True
        print(f"Simulating save bio for user {self.current_user['id']}: '{new_bio}'")

        if success:
            # Update internal user data (important!)
            self.current_user["bio"] = new_bio
            # Update display label
            if new_bio:
                self.bio_display_label.setText(new_bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")

            # Switch back to display mode
            self.toggle_bio_edit(edit_mode=False)
            AnimatedMessageBox.showInformation(self, "成功", "个人简介已更新！")
            # Emit signal if needed (e.g., if other parts of UI depend on bio)
            # self.user_updated.emit(self.current_user)
        else:
            AnimatedMessageBox.showWarning(self, "失败", "无法保存个人简介，请稍后重试。")
