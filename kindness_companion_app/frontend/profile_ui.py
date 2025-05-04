# TODO: 实现用户设置界面 (未来可扩展)
import os
import logging # Add this import at the top
from pathlib import Path
from datetime import datetime # Import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy, QTextEdit,
    QFileDialog, QScrollArea, QSpacerItem, QInputDialog # Removed QCheckBox
)
# Import QByteArray and potentially QBuffer, QIODevice for resizing
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QBitmap, QPainterPath

# Import the custom message box and dialogs
from .widgets.animated_message_box import AnimatedMessageBox
from .password_dialog import PasswordDialog
# Import the newly created widgets
from .widgets.stats_achievements_widget import StatsAchievementsWidget
from .widgets.account_actions_widget import AccountActionsWidget


class ProfileWidget(QWidget):
    """
    Widget for displaying and editing user profile. Now uses sub-widgets for different sections.
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

        # Initialize UI elements for profile info (kept in this widget)
        self.avatar_label = None
        self.username_label = None
        self.reg_date_label = None
        self.bio_display_label = None
        self.bio_edit = None
        self.edit_bio_button = None
        self.save_bio_button = None
        self.cancel_bio_button = None
        self.change_avatar_button = None # Added

        # Instantiate the sub-widgets
        self.stats_achievements_widget = StatsAchievementsWidget(
            self.user_manager, self.progress_tracker, self.challenge_manager
        )
        self.account_actions_widget = AccountActionsWidget(self.user_manager)

        # Connect signals from sub-widgets
        self.account_actions_widget.logout_requested.connect(self.user_logged_out)
        self.account_actions_widget.delete_account_requested.connect(self._handle_delete_account)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface using sub-widgets."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)

        # Title Frame (remains the same)
        title_frame = QFrame()
        title_frame.setObjectName("title_frame")
        title_frame.setStyleSheet("""
            QFrame#title_frame {
                background-color: rgba(40, 40, 40, 0.95);
                border-radius: 18px;
                padding: 15px;
                margin-bottom: 25px;
                border: 1px solid rgba(80, 80, 80, 0.8);
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 12, 15, 12)
        icon_label = QLabel()
        icon = QIcon(":/icons/user.svg")
        if not icon.isNull():
            pixmap = icon.pixmap(QSize(32, 32))
            icon_label.setPixmap(pixmap)
        title_layout.addWidget(icon_label)
        self.title_label = QLabel("个人信息")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel#title_label {
                font-size: 28px;
                font-weight: bold;
                color: #FF9800;
                padding: 10px;
                letter-spacing: 1.5px;
            }
        """)
        title_layout.addWidget(self.title_label)
        self.main_layout.addWidget(title_frame)

        # Scroll Area (remains the same)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical { background: rgba(30, 30, 30, 0.5); width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: rgba(80, 80, 80, 0.7); min-height: 20px; border-radius: 6px; }
            QScrollBar:horizontal { background: rgba(30, 30, 30, 0.5); height: 12px; border-radius: 6px; }
            QScrollBar::handle:horizontal { background: rgba(80, 80, 80, 0.7); min-width: 20px; border-radius: 6px; }
        """)

        # Content Container (remains the same)
        content_container = QWidget()
        content_container.setObjectName("content_container")
        content_container.setStyleSheet("""
            QWidget#content_container {
                background-color: rgba(30, 30, 30, 0.7);
                border-radius: 18px;
                border: 1px solid rgba(70, 70, 70, 0.8);
            }
        """)
        container_layout = QVBoxLayout(content_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)
        content_container.setMinimumWidth(800)

        # Main content layout (Horizontal)
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Setup the profile info section (kept in this widget)
        self.setup_profile_info_section() # Renamed from setup_profile_info

        # Add profile info group and stats/achievements widget to the horizontal layout
        self.content_layout.addWidget(self.profile_group, 40) # Profile info takes 40%
        self.content_layout.addWidget(self.stats_achievements_widget, 60) # Stats/Achievements takes 60%

        # Add content layout to the container
        container_layout.addLayout(self.content_layout)

        # Add Account actions below the main content
        container_layout.addWidget(self.account_actions_widget)

        # Set scroll area content
        scroll_area.setWidget(content_container)

        # Add scroll area to main layout
        self.main_layout.addWidget(scroll_area)

        # No need for setup_action_buttons() call here anymore

    def setup_profile_info_section(self):
        """Set up the profile information section (avatar, username, bio)."""
        self.profile_group = QGroupBox("基本信息")
        self.profile_group.setObjectName("profile_group")
        self.profile_group.setStyleSheet("""
            QGroupBox#profile_group {
                font-weight: bold; font-size: 22px; border-radius: 18px;
                background-color: rgba(35, 35, 35, 0.9); border: 1px solid rgba(80, 80, 80, 0.7);
                padding-top: 35px; color: #FF9800;
            }
        """)
        self.profile_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # Changed vertical policy
        self.profile_group.setMinimumWidth(300)

        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setContentsMargins(25, 30, 25, 25)
        profile_layout.setSpacing(25)

        # --- Avatar Area --- (Simplified, kept styling from previous version)
        avatar_frame = QFrame()
        avatar_frame.setObjectName("avatar_frame")
        avatar_frame.setStyleSheet("""
            QFrame#avatar_frame {
                background-color: rgba(45, 45, 45, 0.8); border-radius: 24px; padding: 25px;
                border: 1px solid rgba(90, 90, 90, 0.7); margin: 8px;
            }
        """)
        avatar_layout = QGridLayout(avatar_frame)
        avatar_layout.setContentsMargins(15, 15, 15, 15); avatar_layout.setSpacing(15)
        avatar_layout.setColumnStretch(0, 1); avatar_layout.setColumnStretch(1, 2)

        avatar_container_frame = QFrame()
        avatar_container_frame.setObjectName("avatar_container")
        avatar_container_frame.setStyleSheet("background-color: transparent; border: none;")
        avatar_container = QVBoxLayout(avatar_container_frame)
        avatar_container.setAlignment(Qt.AlignCenter); avatar_container.setContentsMargins(5, 5, 5, 5); avatar_container.setSpacing(10)

        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatar_label")
        self.avatar_label.setMinimumSize(140, 140); self.avatar_label.setMaximumSize(180, 180)
        self.avatar_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel#avatar_label { border: 3px solid #FF9800; border-radius: 90px; background-color: #333333; padding: 3px; }
        """)
        avatar_container.addWidget(self.avatar_label, 0, Qt.AlignCenter)

        self.change_avatar_button = QPushButton("更换头像")
        self.change_avatar_button.setIcon(QIcon(":/icons/image.svg")); self.change_avatar_button.setIconSize(QSize(16, 16))
        self.change_avatar_button.clicked.connect(self.change_avatar)
        self.change_avatar_button.setFixedHeight(32); self.change_avatar_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.change_avatar_button.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: #222; border-radius: 16px; padding: 5px 10px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #FFA726; } QPushButton:pressed { background-color: #FB8C00; }
        """)
        avatar_container.addWidget(self.change_avatar_button, 0, Qt.AlignCenter)
        avatar_layout.addWidget(avatar_container_frame, 0, 0, Qt.AlignCenter)

        # --- User Info Area --- (Simplified, kept styling)
        user_info_frame = QFrame()
        user_info_frame.setObjectName("user_info_frame")
        user_info_frame.setStyleSheet("""
            QFrame#user_info_frame { background-color: rgba(35, 35, 35, 0.5); border-radius: 10px; border: 1px solid rgba(60, 60, 60, 0.5); padding: 5px; }
        """)
        user_info_container = QVBoxLayout(user_info_frame)
        user_info_container.setAlignment(Qt.AlignVCenter | Qt.AlignLeft); user_info_container.setContentsMargins(10, 10, 10, 10); user_info_container.setSpacing(8)

        username_title = QLabel("用户名"); username_title.setStyleSheet("color: #bbb; font-size: 16px; font-weight: bold;")
        user_info_container.addWidget(username_title)
        self.username_label = QLabel("N/A"); self.username_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 24px;")
        self.username_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); self.username_label.setWordWrap(True)
        user_info_container.addWidget(self.username_label)
        separator = QFrame(); separator.setFrameShape(QFrame.HLine); separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555; margin: 8px 0;"); separator.setMaximumHeight(2)
        user_info_container.addWidget(separator)
        reg_date_title = QLabel("注册日期"); reg_date_title.setStyleSheet("color: #bbb; font-size: 16px; font-weight: bold;")
        user_info_container.addWidget(reg_date_title)
        self.reg_date_label = QLabel("N/A"); self.reg_date_label.setStyleSheet("font-weight: bold; color: #4FC3F7; font-size: 20px;")
        user_info_container.addWidget(self.reg_date_label)
        avatar_layout.addWidget(user_info_frame, 0, 1)
        profile_layout.addWidget(avatar_frame)

        # --- Bio Area --- (Simplified, kept styling)
        bio_frame = QFrame()
        bio_frame.setObjectName("bio_frame")
        bio_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bio_frame.setStyleSheet("""
            QFrame#bio_frame { background-color: rgba(40, 40, 40, 0.7); border-radius: 15px; padding: 15px; border: 1px solid rgba(80, 80, 80, 0.6); margin: 5px; }
        """)
        bio_layout = QVBoxLayout(bio_frame)
        bio_layout.setContentsMargins(15, 15, 15, 15); bio_layout.setSpacing(10)
        bio_header = QHBoxLayout(); bio_header.setSpacing(8); bio_header.setContentsMargins(0, 0, 0, 5)
        bio_icon = QLabel(); icon = QIcon(":/icons/edit-3.svg")
        if not icon.isNull(): bio_icon.setPixmap(icon.pixmap(QSize(18, 18)))
        bio_header.addWidget(bio_icon)
        bio_title = QLabel("个人简介"); bio_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #FF9800;")
        bio_header.addWidget(bio_title); bio_header.addStretch()
        self.edit_bio_button = QPushButton("编辑"); self.edit_bio_button.setIcon(QIcon(":/icons/edit-2.svg")); self.edit_bio_button.setIconSize(QSize(16, 16))
        self.edit_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        self.edit_bio_button.setFixedSize(80, 32)
        self.edit_bio_button.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; border-radius: 16px; padding: 5px 10px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #FFA726; } QPushButton:pressed { background-color: #FB8C00; }
        """)
        bio_header.addWidget(self.edit_bio_button)
        bio_layout.addLayout(bio_header)

        self.bio_display_label = QLabel("这个人很神秘，什么也没留下...")
        self.bio_display_label.setObjectName("bio_display"); self.bio_display_label.setWordWrap(True)
        self.bio_display_label.setAlignment(Qt.AlignTop | Qt.AlignLeft); self.bio_display_label.setMinimumHeight(100)
        self.bio_display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bio_display_label.setStyleSheet("""
            QLabel#bio_display { background-color: rgba(35, 35, 35, 0.9); border-radius: 12px; padding: 15px; color: #f5f5f5; font-size: 16px; border: 1px solid rgba(80, 80, 80, 0.7); line-height: 150%; }
        """)
        self.bio_edit = QTextEdit(); self.bio_edit.setObjectName("bio_edit"); self.bio_edit.setPlaceholderText("在这里编辑您的个人简介...")
        self.bio_edit.setVisible(False); self.bio_edit.setMinimumHeight(100); self.bio_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bio_edit.setStyleSheet("""
            QTextEdit#bio_edit { background-color: rgba(35, 35, 35, 0.9); border-radius: 12px; padding: 15px; color: #f5f5f5; font-size: 16px; border: 2px solid #FF9800; line-height: 150%; }
        """)
        bio_button_layout = QHBoxLayout(); bio_button_layout.setSpacing(8); bio_button_layout.setContentsMargins(0, 5, 0, 0); bio_button_layout.addStretch(1)
        self.save_bio_button = QPushButton("保存"); self.save_bio_button.setIcon(QIcon(":/icons/save.svg")); self.save_bio_button.setIconSize(QSize(14, 14))
        self.save_bio_button.setVisible(False); self.save_bio_button.clicked.connect(self.save_bio); self.save_bio_button.setFixedSize(70, 28)
        self.save_bio_button.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; border-radius: 14px; padding: 4px 8px; font-size: 12px; }
            QPushButton:hover { background-color: #66BB6A; } QPushButton:pressed { background-color: #43A047; }
        """)
        self.cancel_bio_button = QPushButton("取消"); self.cancel_bio_button.setIcon(QIcon(":/icons/x.svg")); self.cancel_bio_button.setIconSize(QSize(14, 14))
        self.cancel_bio_button.setVisible(False); self.cancel_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        self.cancel_bio_button.setFixedSize(70, 28)
        self.cancel_bio_button.setStyleSheet("""
            QPushButton { background-color: #F44336; color: white; border-radius: 14px; padding: 4px 8px; font-size: 12px; }
            QPushButton:hover { background-color: #EF5350; } QPushButton:pressed { background-color: #E53935; }
        """)
        bio_button_layout.addWidget(self.cancel_bio_button); bio_button_layout.addWidget(self.save_bio_button)
        bio_layout.addWidget(self.bio_display_label); bio_layout.addWidget(self.bio_edit); bio_layout.addLayout(bio_button_layout)
        profile_layout.addWidget(bio_frame)

        # Add a spacer at the bottom of the profile section to push content up
        profile_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))


    # Removed setup_stats() - handled by StatsAchievementsWidget
    # Removed setup_action_buttons() - handled by AccountActionsWidget

    def _set_circular_avatar(self, avatar_data): # Parameter changed to avatar_data (bytes or None)
        """Loads an image from bytes, makes it circular, and sets it on the avatar_label."""
        pixmap = QPixmap()
        loaded = False
        if avatar_data:
            loaded = pixmap.loadFromData(avatar_data)

        if not loaded:
            logging.warning(f"Could not load avatar from data. Using default resource.")
            pixmap = QPixmap(":/images/profilePicture.png")
            if pixmap.isNull():
                 logging.error("Default avatar resource ':/images/profilePicture.png' is also missing!")
                 pixmap = QPixmap(140, 140)
                 pixmap.fill(Qt.gray)

        size = 140
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        final_pixmap = QPixmap(size, size)
        final_pixmap.fill(Qt.transparent)

        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        x_offset = (scaled_pixmap.width() - size) // 2
        y_offset = (scaled_pixmap.height() - size) // 2
        painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
        painter.end()

        self.avatar_label.setPixmap(final_pixmap)

    # Removed toggle_ai_consent() - handled by AISettingsWidget

    @Slot(dict)
    def set_user(self, user):
        """Set the current user and update UI elements, delegating to sub-widgets."""
        logger = logging.getLogger(__name__)
        logger.info(f"ProfileWidget.set_user called. User is None: {user is None}")
        self.current_user = user

        # Update profile info section (avatar, username, bio, reg date)
        if user:
            logger.debug(f"User data: {user}")
            self.username_label.setText(user.get("username", "N/A"))

            # --- Load and Format Registration Date ---
            reg_date_str_raw = user.get("registration_date")
            logger.info(f"Raw registration_date from user dict: '{reg_date_str_raw}' (Type: {type(reg_date_str_raw)})" )
            final_display_text = "未知"
            if reg_date_str_raw:
                try:
                    timestamp_part = str(reg_date_str_raw).split('.')[0].split('+')[0]
                    dt_object = datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
                    final_display_text = dt_object.strftime('%Y-%m-%d')
                    logger.info(f"Successfully parsed and formatted date: {final_display_text}")
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Could not parse registration date '{reg_date_str_raw}': {e}. Falling back to '未知'.")
            else:
                logger.warning("registration_date key missing or value is None/empty in user dict. Setting text to '未知'.")
            logger.info(f"Final text to set on reg_date_label: '{final_display_text}'")
            self.reg_date_label.setText(final_display_text)

            # --- Load Bio ---
            bio = user.get("bio", "")
            if bio:
                self.bio_display_label.setText(bio)
                self.bio_edit.setText(bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")
                self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

            # --- Load Avatar ---
            avatar_data = user.get("avatar")
            self._set_circular_avatar(avatar_data)

            # Enable profile editing buttons
            self.change_avatar_button.setEnabled(True)
            self.edit_bio_button.setEnabled(True)

        else: # User is None (logout or initial state)
            logger.info("User is None. Resetting profile fields.")
            self.username_label.setText("N/A")
            self.reg_date_label.setText("N/A")
            self.bio_display_label.setText("请先登录")
            self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False)
            self._set_circular_avatar(None) # Reset avatar

            # Disable profile editing buttons
            self.change_avatar_button.setEnabled(False)
            self.edit_bio_button.setEnabled(False)
            # Ensure save/cancel bio buttons are hidden and disabled
            self.save_bio_button.setVisible(False)
            self.cancel_bio_button.setVisible(False)
            self.save_bio_button.setEnabled(False)
            self.cancel_bio_button.setEnabled(False)


        # Delegate user setting to sub-widgets
        self.stats_achievements_widget.set_user(user)
        self.account_actions_widget.set_user(user)


    # Removed load_stats() - handled by StatsAchievementsWidget
    # Removed reset_stats() - partially handled by set_user(None), partially by StatsAchievementsWidget

    # Removed load_achievements() - handled by StatsAchievementsWidget
    # Removed clear_achievements() - handled by StatsAchievementsWidget

    # Removed show_password_dialog() - handled by AccountActionsWidget

    # Keep update_user_info as it updates the main user dict and emits signal
    def update_user_info(self, user_info):
        """
        Update user information in the application.

        Args:
            user_info (dict): Updated user information
        """
        self.current_user = user_info
        self.user_updated.emit(user_info) # Emit signal for main window etc.

    # Removed logout() - handled by AccountActionsWidget signal connection

    # --- Bio Editing Methods (remain the same) ---
    @Slot()
    def toggle_bio_edit(self, edit_mode=None):
        """Toggle between displaying and editing the bio."""
        if edit_mode is None:
            edit_button_visible = self.edit_bio_button.isVisible()
            currently_editing = not edit_button_visible
            edit_mode = not currently_editing

        # Only proceed if a user is logged in
        can_edit = self.current_user is not None

        self.bio_display_label.setVisible(not edit_mode)
        self.edit_bio_button.setVisible(not edit_mode and can_edit) # Hide if not logged in

        self.bio_edit.setVisible(edit_mode and can_edit)
        self.save_bio_button.setVisible(edit_mode and can_edit)
        self.cancel_bio_button.setVisible(edit_mode and can_edit)

        # Enable/disable buttons based on login status as well
        self.edit_bio_button.setEnabled(can_edit)
        self.save_bio_button.setEnabled(can_edit)
        self.cancel_bio_button.setEnabled(can_edit)


        if not edit_mode: # If switching back to display mode
             current_bio = self.bio_display_label.text()
             if current_bio == "这个人很神秘，什么也没留下..." or current_bio == "请先登录":
                 self.bio_edit.setText("")
             else:
                 self.bio_edit.setText(current_bio)
        elif can_edit: # Only focus if entering edit mode AND logged in
            self.bio_edit.setFocus()

    @Slot()
    def save_bio(self):
        """Save the edited bio."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "用户未登录")
            return

        new_bio = self.bio_edit.toPlainText().strip()

        success = self.user_manager.update_profile(self.current_user["id"], bio=new_bio)

        if success:
            self.current_user["bio"] = new_bio
            if new_bio:
                self.bio_display_label.setText(new_bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")

            self.toggle_bio_edit(edit_mode=False)
            AnimatedMessageBox.showInformation(self, "成功", "个人简介已更新！")
            self.user_updated.emit(self.current_user) # Emit signal with updated user
        else:
            AnimatedMessageBox.showWarning(self, "失败", "无法保存个人简介，请稍后重试。")

    # --- Avatar Change Method (remains the same) ---
    @Slot()
    def change_avatar(self):
        """Opens a file dialog, reads image data, saves blob to DB, and updates profile."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "请先登录")
            return

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;All Files (*)")
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]
                try:
                    with open(source_path, 'rb') as f:
                        avatar_bytes = f.read()

                    max_dimension = 256
                    quality = 85
                    save_format = "PNG"

                    temp_pixmap = QPixmap()
                    if temp_pixmap.loadFromData(avatar_bytes):
                        if temp_pixmap.width() > max_dimension or temp_pixmap.height() > max_dimension:
                            scaled_pixmap = temp_pixmap.scaled(max_dimension, max_dimension, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            byte_array = QByteArray()
                            buffer = QBuffer(byte_array)
                            buffer.open(QIODevice.WriteOnly)
                            if save_format == "JPG":
                                scaled_pixmap.save(buffer, "JPG", quality)
                            else:
                                scaled_pixmap.save(buffer, "PNG")
                            avatar_bytes = byte_array.data()
                            logging.info(f"Resized avatar to fit within {max_dimension}x{max_dimension} ({len(avatar_bytes)} bytes)")
                        else:
                             logging.info(f"Avatar size is within limits ({len(avatar_bytes)} bytes)")
                    else:
                        AnimatedMessageBox.showCritical(self, "错误", "无法加载所选图片数据。")
                        return

                    success = self.user_manager.update_profile(
                        self.current_user["id"],
                        avatar_data=avatar_bytes
                    )

                    if success:
                        self.current_user["avatar"] = avatar_bytes
                        self._set_circular_avatar(avatar_bytes)
                        AnimatedMessageBox.showInformation(self, "成功", "头像已更新！")
                        self.user_updated.emit(self.current_user) # Pass updated user dict
                    else:
                        AnimatedMessageBox.showWarning(self, "失败", "无法更新数据库中的头像数据。")

                except FileNotFoundError:
                     AnimatedMessageBox.showCritical(self, "错误", f"无法找到文件: {source_path}")
                except Exception as e:
                    logging.error(f"Error changing avatar: {e}")
                    AnimatedMessageBox.showCritical(self, "错误", f"更换头像时发生错误: {e}")

    # Removed request_delete_account() - handled by AccountActionsWidget signal connection

    # --- Signal Handlers for Sub-widgets ---
    @Slot()
    def _handle_delete_account(self):
        """Handles the delete account request after confirmation from AccountActionsWidget."""
        if not self.current_user:
            return # Should not happen if button was enabled, but check anyway

        username = self.current_user.get("username", "")
        user_id = self.current_user.get("id")

        # Ask for password confirmation (moved from AccountActionsWidget for final check here)
        password, ok = QInputDialog.getText(
            self,
            "确认注销账号",
            f"请输入您的密码以确认永久删除账号 \"{username}\"：",
            QLineEdit.Password
        )

        if not ok or not password:
            logging.info(f"Account deletion cancelled by user {username} (ID: {user_id}) at password prompt.")
            return

        # Call backend to delete account
        try:
            success = self.user_manager.delete_user_account(user_id, password)

            if success:
                AnimatedMessageBox.showInformation(self, "账号已注销", f"账号 \"{username}\" 已被永久删除。")
                # Trigger logout process
                QTimer.singleShot(10, self.user_logged_out.emit)
            else:
                # Password might be incorrect, or other backend error
                AnimatedMessageBox.showWarning(self, "注销失败", "密码不正确或发生内部错误，无法注销账号。")
        except Exception as e:
            logging.error(f"Error during account deletion for user {user_id}: {e}")
            AnimatedMessageBox.showCritical(self, "注销出错", f"注销过程中发生意外错误：{e}")
