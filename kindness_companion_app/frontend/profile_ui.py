import os
import logging # Add this import at the top
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy, QTextEdit,
    QFileDialog, QScrollArea, QSpacerItem # Added QScrollArea, QSpacerItem
)
# Import QByteArray and potentially QBuffer, QIODevice for resizing
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QBitmap, QPainterPath
# shutil might not be needed anymore if we don't copy files
# import shutil

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
        # Add elements for dynamic achievements
        self.achievements_group = None
        self.achievements_scroll_area = None
        self.achievements_container = None
        self.achievements_layout = None
        self.achievements_placeholder = None
        self.achievements_spacer = None


        self.setup_ui()

    # ... (setup_ui, setup_profile_info remain largely the same) ...
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
        self.profile_group.setMinimumWidth(350)
        self.profile_group.setMaximumWidth(450) # Keep profile info width fixed

        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setContentsMargins(15, 20, 15, 20)
        profile_layout.setSpacing(15)

        # --- Avatar ---
        avatar_layout = QVBoxLayout() # Use QVBoxLayout for label and button
        avatar_layout.setAlignment(Qt.AlignCenter)

        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatar_label")
        self.avatar_label.setFixedSize(80, 80)
        self.avatar_label.setAlignment(Qt.AlignCenter) # Center the pixmap within the label
        # Default avatar set in set_user or reset_stats

        self.change_avatar_button = QPushButton("更换头像")
        self.change_avatar_button.setIcon(QIcon(":/icons/image.svg")) # Optional icon
        self.change_avatar_button.clicked.connect(self.change_avatar)
        self.change_avatar_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # Prevent stretching

        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addSpacing(5) # Space between avatar and button
        avatar_layout.addWidget(self.change_avatar_button)

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
        # Use lambda to ensure no arguments are passed from clicked signal
        self.edit_bio_button.clicked.connect(lambda: self.toggle_bio_edit())

        self.save_bio_button = QPushButton("保存")
        self.save_bio_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_bio_button.setVisible(False) # 初始隐藏
        self.save_bio_button.clicked.connect(self.save_bio)

        self.cancel_bio_button = QPushButton("取消")
        self.cancel_bio_button.setVisible(False) # 初始隐藏
        # Use lambda to ensure no arguments are passed from clicked signal
        self.cancel_bio_button.clicked.connect(lambda: self.toggle_bio_edit()) # 取消也切换状态

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
        # Allow stats group to expand vertically
        self.stats_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        stats_layout = QVBoxLayout(self.stats_group)
        stats_layout.setSpacing(15) # Add spacing between summary and achievements

        # --- Summary layout (remains the same) ---
        summary_group = QGroupBox("概览") # Optional: Group summary stats
        summary_layout = QGridLayout(summary_group)
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

        stats_layout.addWidget(summary_group) # Add the summary group

        # --- Achievements Section (Replaces old hardcoded progress bars) ---
        self.achievements_group = QGroupBox("我的成就")
        # Allow achievements group to expand vertically
        self.achievements_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        achievements_group_layout = QVBoxLayout(self.achievements_group)

        # Scroll Area for Achievements
        self.achievements_scroll_area = QScrollArea()
        self.achievements_scroll_area.setWidgetResizable(True)
        self.achievements_scroll_area.setObjectName("achievements_scroll_area") # For potential styling
        self.achievements_scroll_area.setFrameShape(QFrame.NoFrame) # Remove border

        # Container Widget inside Scroll Area
        self.achievements_container = QWidget()
        self.achievements_scroll_area.setWidget(self.achievements_container)

        # Layout for the Container Widget (where achievements will be added)
        self.achievements_layout = QVBoxLayout(self.achievements_container)
        self.achievements_layout.setAlignment(Qt.AlignTop) # Align items to the top
        self.achievements_layout.setSpacing(8) # Spacing between achievements
        self.achievements_layout.setContentsMargins(5, 5, 5, 5) # Add some padding

        # Placeholder Label
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setAlignment(Qt.AlignCenter)
        self.achievements_layout.addWidget(self.achievements_placeholder)

        # Spacer Item
        self.achievements_spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.achievements_layout.addSpacerItem(self.achievements_spacer)

        achievements_group_layout.addWidget(self.achievements_scroll_area) # Add scroll area to group
        stats_layout.addWidget(self.achievements_group) # Add achievements group to main stats layout


    # ... (_set_circular_avatar, set_user remain the same) ...
    def _set_circular_avatar(self, avatar_data): # Parameter changed to avatar_data (bytes or None)
        """Loads an image from bytes, makes it circular, and sets it on the avatar_label."""
        pixmap = QPixmap()
        loaded = False
        if avatar_data:
            # Load pixmap from byte data
            loaded = pixmap.loadFromData(avatar_data)

        if not loaded:
            # print(f"Warning: Could not load avatar from data. Using default resource.")
            logging.warning(f"Could not load avatar from data. Using default resource.") # Use logging
            # Fallback to default resource if data is None or loading fails
            pixmap = QPixmap(":/images/profilePicture.png")
            if pixmap.isNull():
                 # print("ERROR: Default avatar resource ':/images/profilePicture.png' is also missing!")
                 logging.error("Default avatar resource ':/images/profilePicture.png' is also missing!") # Use logging
                 # Optionally create a plain colored circle as ultimate fallback
                 pixmap = QPixmap(80, 80)
                 pixmap.fill(Qt.gray)


        # Scale the pixmap first
        size = 80
        # Use KeepAspectRatioByExpanding to fill the circle, then clip
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # --- Alternative: Draw clipped pixmap onto a new transparent pixmap ---
        final_pixmap = QPixmap(size, size)
        final_pixmap.fill(Qt.transparent) # Start with a transparent pixmap

        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a circular clipping path
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        # Calculate offsets to draw the scaled pixmap centered
        x_offset = (scaled_pixmap.width() - size) // 2
        y_offset = (scaled_pixmap.height() - size) // 2

        # Draw the (potentially larger) scaled pixmap onto the target pixmap, clipped
        painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
        painter.end()

        # Set the final circular pixmap
        self.avatar_label.setPixmap(final_pixmap)


    @Slot(dict)
    def set_user(self, user):
        """Set the current user and update UI elements using avatar data."""
        self.current_user = user

        if user:
            # Update profile info
            self.username_label.setText(user.get("username", "N/A"))

            # --- Load Registration Date ---
            reg_date_str = user.get("registration_date", "未知")
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

            # --- Load Avatar from BLOB data ---
            avatar_data = user.get("avatar") # Get bytes or None
            self._set_circular_avatar(avatar_data) # Use the helper method

            # Load stats (which now includes loading achievements)
            self.load_stats()
        else:
            # Clear profile info
            self.username_label.setText("N/A")
            # Reset reg date
            self.reg_date_label.setText("N/A")
            # Reset bio
            self.bio_display_label.setText("请先登录")
            self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

            # Reset avatar to default circular avatar
            self._set_circular_avatar(None) # Pass None to use default

            # Reset stats and clear achievements
            self.reset_stats()


    def load_stats(self):
        """Load and display user stats and achievements."""
        if not self.current_user:
            return

        user_id = self.current_user["id"] # Get user_id once

        # Get all user check-ins
        # check_ins = self.progress_tracker.get_all_user_check_ins(user_id) # Not directly needed for summary stats
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        self.total_label.setText(str(total_check_ins))

        # Calculate longest streak across all challenges
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(user_id)
        self.streak_label.setText(str(longest_streak))

        # Get subscribed challenges count
        challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(challenges)
        self.challenges_label.setText(str(subscribed_challenges_count))

        # Load dynamic achievements using the new method
        self.load_achievements()


    def reset_stats(self):
        """Reset stats and achievements, and clear profile fields on logout."""
        # Reset stats labels
        self.total_label.setText("0")
        self.streak_label.setText("0")
        self.challenges_label.setText("0")

        # Clear dynamic achievements
        self.clear_achievements()

        # Clear profile fields (remains the same)
        if self.username_label: self.username_label.setText("N/A")
        if self.avatar_label:
             self._set_circular_avatar(None) # Use helper with None for default
        if self.reg_date_label: self.reg_date_label.setText("N/A")
        if self.bio_display_label: self.bio_display_label.setText("请先登录")
        if self.bio_edit: self.bio_edit.setText("")
        self.toggle_bio_edit(edit_mode=False) # Ensure display mode

    # --- New Achievement Methods (Adapted from progress_ui.py) ---

    def load_achievements(self):
        """Load and display user achievements/badges within the scroll area."""
        if not self.current_user:
            self.clear_achievements() # Clear if no user
            return

        user_id = self.current_user["id"]

        # --- Fetch achievement data ---
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(user_id)
        subscribed_challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(subscribed_challenges)
        # Fetch category counts if needed by achievements_data
        eco_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "环保")
        community_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "社区服务")

        # --- Define achievements_data (Mirrors progress_ui.py) ---
        achievements_data = [
            # Check-in Milestones
            {"name": "善行初学者", "target": 10, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善行践行者", "target": 50, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善意大师", "target": 100, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            # Streak Milestones
            {"name": "坚持不懈", "target": 7, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "毅力之星", "target": 14, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "恒心典范", "target": 30, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            # Subscription Milestones
            {"name": "探索之心", "target": 5, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "挑战收藏家", "target": 10, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "领域专家", "target": 20, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            # Category Milestones
            {"name": "环保卫士", "target": 10, "current": eco_check_ins, "unit": "次环保行动", "icon": ":/icons/leaf.svg"},
            {"name": "社区之星", "target": 10, "current": community_check_ins, "unit": "次社区服务", "icon": ":/icons/users.svg"},
            # Generic Target Milestones
            {"name": "目标达成者", "target": 25, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/target.svg"},
            {"name": "闪耀新星", "target": 15, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/star.svg"},
        ]

        # --- Clear previous achievements ---
        self.clear_achievements()

        achievements_added = False
        # --- Populate achievements layout ---
        for ach in achievements_data:
            # Only display achievements with a positive target
            if ach["target"] > 0:
                achievements_added = True
                ach_layout = QHBoxLayout()
                ach_layout.setSpacing(10)

                # Icon Label
                icon_label = QLabel()
                icon_path = ach.get("icon", None)
                if icon_path:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        pixmap = icon.pixmap(QSize(20, 20))
                        icon_label.setPixmap(pixmap)
                    else:
                        logging.warning(f"Failed to load achievement icon: {icon_path}")
                        icon_label.setText("?")
                        icon_label.setFixedSize(20, 20)
                        icon_label.setAlignment(Qt.AlignCenter)
                else:
                    # Keep space consistent even without icon
                    icon_label.setFixedSize(20, 20)

                icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                ach_layout.addWidget(icon_label)

                # Title Label
                title_label = QLabel(ach["name"])
                title_label.setMinimumWidth(70) # Adjust width if needed
                title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

                # Progress Bar
                progress_bar = QProgressBar()
                progress_bar.setRange(0, ach['target'])
                display_value = min(ach['current'], ach['target'])
                progress_bar.setValue(display_value)
                progress_bar.setFormat(f"{display_value}/{ach['target']} {ach['unit']}")
                progress_bar.setAlignment(Qt.AlignCenter)
                progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

                # Styling (same as progress_ui.py)
                if ach["current"] >= ach["target"]:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                    """)
                else:
                     progress_bar.setStyleSheet("""
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                        QProgressBar::chunk { background-color: #2196F3; border-radius: 4px; width: 10px; margin: 0.5px; }
                     """)

                ach_layout.addWidget(title_label)
                ach_layout.addWidget(progress_bar)

                # Insert the new achievement layout *before* the spacer
                insert_index = self.achievements_layout.count() - 1 # Index before the spacer
                self.achievements_layout.insertLayout(insert_index, ach_layout)

        # --- Manage placeholder visibility ---
        if achievements_added:
            self.achievements_placeholder.hide()
            # Ensure spacer pushes content up
            self.achievements_spacer.changeSize(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            self.achievements_placeholder.setText("暂无成就，继续努力吧！")
            self.achievements_placeholder.show()
            # Collapse spacer if no achievements
            self.achievements_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)

    def clear_achievements(self):
        """Clear the achievements display area, keeping placeholder and spacer."""
        if not self.achievements_layout:
            return

        # Remove all items except the placeholder (index 0) and spacer (last index)
        # Iterate backwards to avoid index issues while removing
        layout_count = self.achievements_layout.count()
        if layout_count > 2: # If there are achievements added (more than placeholder + spacer)
            for i in range(layout_count - 2, 0, -1): # Iterate from second-to-last down to index 1
                item = self.achievements_layout.takeAt(i)
                if item:
                    # Remove layout
                    if item.layout():
                        # Recursively delete widgets within the layout
                        while item.layout().count():
                            child = item.layout().takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()
                        item.layout().deleteLater()
                    # Remove widget
                    elif item.widget():
                        item.widget().deleteLater()
                    # Remove spacer (shouldn't happen here, but good practice)
                    elif item.spacerItem():
                        pass # Don't delete the main spacer here
                    del item

        # Ensure placeholder is visible and spacer is collapsed after clearing
        if self.achievements_layout.count() == 2: # Should be placeholder + spacer
            placeholder_item = self.achievements_layout.itemAt(0)
            spacer_item = self.achievements_layout.itemAt(1)

            if placeholder_item and isinstance(placeholder_item.widget(), QLabel) and spacer_item and spacer_item.spacerItem():
                placeholder_item.widget().setText("暂无成就，继续努力吧！") # Reset text just in case
                placeholder_item.widget().show()
                # Collapse spacer when placeholder is shown
                spacer_item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
            else:
                 logging.warning("clear_achievements (profile): Layout structure incorrect after clearing.")
                 # Attempt to reset placeholder anyway
                 if self.achievements_placeholder:
                     self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                     self.achievements_placeholder.show()
                 # Try to find and collapse spacer
                 for i in range(self.achievements_layout.count()):
                     item = self.achievements_layout.itemAt(i)
                     if item and item.spacerItem():
                         item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
                         break
        elif self.achievements_layout.count() == 0: # Should not happen with placeholder/spacer logic
             logging.warning("clear_achievements (profile): Layout became empty, re-adding placeholder and spacer.")
             if self.achievements_placeholder and self.achievements_spacer:
                 self.achievements_layout.addWidget(self.achievements_placeholder)
                 self.achievements_layout.addSpacerItem(self.achievements_spacer)
                 self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                 self.achievements_placeholder.show()
                 self.achievements_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
        else: # Only placeholder or only spacer? Something is wrong.
             logging.warning(f"clear_achievements (profile): {self.achievements_layout.count()} items remain, expected 2.")
             # Ensure placeholder is visible
             if self.achievements_placeholder:
                 self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                 self.achievements_placeholder.show()
             # Try to find and collapse spacer
             for i in range(self.achievements_layout.count()):
                 item = self.achievements_layout.itemAt(i)
                 if item and item.spacerItem():
                     item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
                     break


    # ... (show_password_dialog, update_user_info, logout remain the same) ...
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
            self.reset_stats() # This now also clears achievements
            # Emit signal slightly delayed after confirmation
            QTimer.singleShot(10, self.user_logged_out.emit)


    # --- Bio Editing Methods (remain the same) ---
    @Slot() # Changed from @Slot(bool)
    def toggle_bio_edit(self, edit_mode=None):
        """Toggle between displaying and editing the bio."""
        logger = logging.getLogger(__name__) # Get logger instance
        # logger.info(f"toggle_bio_edit called with edit_mode={edit_mode}") # Reduce verbosity

        if edit_mode is None:
            # Toggle based on current visibility of edit button
            edit_button_visible = self.edit_bio_button.isVisible()
            # logger.info(f"  edit_bio_button.isVisible() = {edit_button_visible}")
            currently_editing = not edit_button_visible
            edit_mode = not currently_editing
            # logger.info(f"  Determined currently_editing={currently_editing}, setting edit_mode={edit_mode}")
        # else:
            # logger.info(f"  Using provided edit_mode={edit_mode}")

        # logger.info(f"  Setting visibility: bio_display={not edit_mode}, edit_button={not edit_mode}, bio_edit={edit_mode}, save_button={edit_mode}, cancel_button={edit_mode}")
        self.bio_display_label.setVisible(not edit_mode)
        self.edit_bio_button.setVisible(not edit_mode)

        self.bio_edit.setVisible(edit_mode)
        self.save_bio_button.setVisible(edit_mode)
        self.cancel_bio_button.setVisible(edit_mode)

        if not edit_mode: # If switching back to display mode
             # logger.info("  Switching back to display mode, resetting bio_edit text.")
             # Reset edit text to current display text in case of cancel
             current_bio = self.bio_display_label.text()
             if current_bio == "这个人很神秘，什么也没留下..." or current_bio == "请先登录":
                 self.bio_edit.setText("")
             else:
                 self.bio_edit.setText(current_bio)
        else:
            # logger.info("  Switching to edit mode.")
            # Optionally set focus to the editor when entering edit mode
            self.bio_edit.setFocus()

    @Slot()
    def save_bio(self):
        """Save the edited bio."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "用户未登录")
            return

        new_bio = self.bio_edit.toPlainText().strip()

        # --- Call backend to update profile ---
        success = self.user_manager.update_profile(self.current_user["id"], bio=new_bio)

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
            # Emit signal if needed
            self.user_updated.emit(self.current_user)
        else:
            AnimatedMessageBox.showWarning(self, "失败", "无法保存个人简介，请稍后重试。")

    # --- Avatar Change Method (remains the same) ---
    @Slot()
    def change_avatar(self):
        """Opens a file dialog, reads image data, saves blob to DB, and updates profile."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "请先登录")
            return

        # Open file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;All Files (*)")
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]

                try:
                    # Read image file into bytes
                    with open(source_path, 'rb') as f:
                        avatar_bytes = f.read()

                    # --- Optional: Image Resizing/Compression before saving ---
                    max_dimension = 256 # Example: Limit to 256x256
                    quality = 85 # JPEG quality if saving as JPG
                    save_format = "PNG" # Or "JPG"

                    temp_pixmap = QPixmap()
                    if temp_pixmap.loadFromData(avatar_bytes):
                        if temp_pixmap.width() > max_dimension or temp_pixmap.height() > max_dimension:
                            scaled_pixmap = temp_pixmap.scaled(max_dimension, max_dimension, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            byte_array = QByteArray()
                            buffer = QBuffer(byte_array)
                            buffer.open(QIODevice.WriteOnly)
                            # Save resized pixmap back to bytes
                            if save_format == "JPG":
                                scaled_pixmap.save(buffer, "JPG", quality)
                            else:
                                scaled_pixmap.save(buffer, "PNG") # PNG is lossless but might be larger
                            avatar_bytes = byte_array.data() # Get bytes from QByteArray
                            logging.info(f"Resized avatar to fit within {max_dimension}x{max_dimension} ({len(avatar_bytes)} bytes)") # Use logging
                        else:
                             logging.info(f"Avatar size is within limits ({len(avatar_bytes)} bytes)") # Use logging
                    else:
                        AnimatedMessageBox.showCritical(self, "错误", "无法加载所选图片数据。")
                        return
                    # --- End Optional Resizing ---

                    # Update database with blob data
                    success = self.user_manager.update_profile(
                        self.current_user["id"],
                        avatar_data=avatar_bytes # Pass the image bytes (potentially resized)
                    )

                    if success:
                        # Update internal user data
                        self.current_user["avatar"] = avatar_bytes
                        # Update the UI
                        self._set_circular_avatar(avatar_bytes)
                        AnimatedMessageBox.showInformation(self, "成功", "头像已更新！")
                        # Emit signal to notify other parts
                        self.user_updated.emit(self.current_user) # Pass updated user dict
                    else:
                        AnimatedMessageBox.showWarning(self, "失败", "无法更新数据库中的头像数据。")

                except FileNotFoundError:
                     AnimatedMessageBox.showCritical(self, "错误", f"无法找到文件: {source_path}")
                except Exception as e:
                    logging.error(f"Error changing avatar: {e}") # Use logging
                    AnimatedMessageBox.showCritical(self, "错误", f"更换头像时发生错误: {e}")
