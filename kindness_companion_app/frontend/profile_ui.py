# TODO: 实现用户设置界面 (未来可扩展)
import os
import logging
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy, QTextEdit,
    QFileDialog, QScrollArea, QSpacerItem, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QBitmap, QPainterPath, QColor

from .widgets.animated_message_box import AnimatedMessageBox
from .password_dialog import PasswordDialog
from .widgets.stats_achievements_widget import StatsAchievementsWidget
from .widgets.account_actions_widget import AccountActionsWidget

logger = logging.getLogger(__name__)

class ProfileWidget(QWidget):
    """
    Widget for displaying and editing user profile. Now uses sub-widgets for different sections.
    """
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

        self.avatar_label = None
        self.username_label = None
        self.reg_date_label = None
        self.bio_display_label = None
        self.bio_edit = None
        self.edit_bio_button = None
        self.save_bio_button = None
        self.cancel_bio_button = None
        self.change_avatar_button = None

        self.stats_achievements_widget = StatsAchievementsWidget(
            self.user_manager, self.progress_tracker, self.challenge_manager
        )
        self.account_actions_widget = AccountActionsWidget(self.user_manager)

        self.account_actions_widget.logout_requested.connect(self.user_logged_out)
        self.account_actions_widget.delete_account_requested.connect(self._handle_delete_account)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface using sub-widgets."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("profile_scroll_area")

        # Content Container
        content_container = QWidget()
        content_container.setObjectName("profile_content_container")

        container_layout = QVBoxLayout(content_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(20)

        # Title Label
        title_label = QLabel("个人资料")
        title_label.setObjectName("profile_title_label") # Keep object name for QSS targeting
        title_label.setAlignment(Qt.AlignLeft)
        container_layout.addWidget(title_label)

        # Main content layout (Vertical)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Setup the profile info section
        self.setup_profile_info_section()

        # Add profile info frame and stats/achievements widget
        # Use a QVBoxLayout with stretch factors to give more space to achievements
        self.content_layout.addWidget(self.profile_info_frame, 1)  # Stretch factor 1
        self.content_layout.addWidget(self.stats_achievements_widget, 3)  # Stretch factor 3 (more space)

        # Add content layout to the container
        container_layout.addLayout(self.content_layout)
        container_layout.addStretch(1)

        # Add Account actions below the main content
        container_layout.addWidget(self.account_actions_widget)

        # Set scroll area content
        scroll_area.setWidget(content_container)
        self.main_layout.addWidget(scroll_area)

    def setup_profile_info_section(self):
        """Set up the profile information section (avatar, username, bio) using a QFrame."""
        self.profile_info_frame = QFrame()
        self.profile_info_frame.setObjectName("profile_info_card") # Keep object name
        self.profile_info_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        profile_layout = QVBoxLayout(self.profile_info_frame)
        profile_layout.setContentsMargins(18, 18, 18, 18)
        profile_layout.setSpacing(15)

        # --- Header Section with Avatar and User Info ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Avatar Container
        avatar_container = QFrame()
        avatar_container.setObjectName("avatar_container") # Keep object name
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setSpacing(8)

        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("profile_avatar_label") # Keep object name
        self.avatar_label.setFixedSize(80, 80)  # Further reduced avatar size
        self.avatar_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(self.avatar_label)

        self.change_avatar_button = QPushButton("更换头像")
        self.change_avatar_button.setObjectName("change_avatar_button") # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.change_avatar_button.clicked.connect(self.change_avatar)
        self.change_avatar_button.setProperty("class", "secondary_button") # Keep class for QSS
        avatar_layout.addWidget(self.change_avatar_button, alignment=Qt.AlignCenter)

        header_layout.addWidget(avatar_container)

        # User Info Container
        user_info_container = QFrame()
        user_info_container.setObjectName("user_info_container") # Keep object name
        user_info_layout = QVBoxLayout(user_info_container)
        user_info_layout.setContentsMargins(0, 5, 0, 5)
        user_info_layout.setSpacing(10)
        user_info_layout.setAlignment(Qt.AlignVCenter)

        # Username with label
        username_layout = QVBoxLayout()
        username_layout.setSpacing(3)

        username_title = QLabel("用户名")
        username_title.setObjectName("profile_label_title") # Keep object name
        username_layout.addWidget(username_title)

        self.username_label = QLabel("N/A")
        self.username_label.setObjectName("username_label") # Keep object name
        username_layout.addWidget(self.username_label)

        user_info_layout.addLayout(username_layout)

        # Registration date with label
        reg_date_layout = QVBoxLayout()
        reg_date_layout.setSpacing(3)

        reg_date_title = QLabel("注册日期")
        reg_date_title.setObjectName("profile_label_title") # Keep object name
        reg_date_layout.addWidget(reg_date_title)

        self.reg_date_label = QLabel("N/A")
        self.reg_date_label.setObjectName("profile_reg_date_label") # Keep object name
        reg_date_layout.addWidget(self.reg_date_label)

        user_info_layout.addLayout(reg_date_layout)

        user_info_layout.addStretch()
        header_layout.addWidget(user_info_container, 1)  # Give it stretch factor

        profile_layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(1)
        profile_layout.addWidget(separator)

        # --- Bio Section ---
        bio_container = QFrame()
        bio_container.setObjectName("profile_bio_container") # Keep object name
        bio_layout = QVBoxLayout(bio_container)
        # Reduce margins to make bio section more compact
        bio_layout.setContentsMargins(0, 3, 0, 3)
        bio_layout.setSpacing(6)

        bio_header_layout = QHBoxLayout()
        bio_title = QLabel("个人简介")
        bio_title.setObjectName("profile_section_title") # Keep object name
        bio_header_layout.addWidget(bio_title)
        bio_header_layout.addStretch()

        self.edit_bio_button = QPushButton("编辑")
        self.edit_bio_button.setObjectName("edit_bio_button") # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.edit_bio_button.setText("编辑")
        self.edit_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        bio_header_layout.addWidget(self.edit_bio_button)
        bio_layout.addLayout(bio_header_layout)

        # Bio content frame
        bio_content_frame = QFrame()
        bio_content_frame.setObjectName("profile_bio_content") # Keep object name
        bio_content_layout = QVBoxLayout(bio_content_frame)
        # Reduce padding to make bio section more compact
        bio_content_layout.setContentsMargins(10, 8, 10, 8)
        bio_content_layout.setSpacing(6)

        self.bio_display_label = QLabel("这个人很神秘，什么也没留下...")
        self.bio_display_label.setObjectName("profile_bio_display") # Keep object name
        self.bio_display_label.setWordWrap(True)
        self.bio_display_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # Reduce minimum height to make bio section more compact
        self.bio_display_label.setMinimumHeight(60)
        self.bio_display_label.setMaximumHeight(80)
        self.bio_display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bio_content_layout.addWidget(self.bio_display_label)

        self.bio_edit = QTextEdit()
        self.bio_edit.setObjectName("profile_bio_edit") # Keep object name
        self.bio_edit.setPlaceholderText("编辑您的个人简介...")
        self.bio_edit.setVisible(False)
        # Reduce minimum height to make bio section more compact
        self.bio_edit.setMinimumHeight(60)
        self.bio_edit.setMaximumHeight(80)
        self.bio_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bio_content_layout.addWidget(self.bio_edit)

        bio_button_layout = QHBoxLayout()
        bio_button_layout.setSpacing(10)
        bio_button_layout.addStretch()

        self.cancel_bio_button = QPushButton("取消")
        self.cancel_bio_button.setObjectName("cancel_bio_button") # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.cancel_bio_button.setVisible(False)
        self.cancel_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        bio_button_layout.addWidget(self.cancel_bio_button)

        self.save_bio_button = QPushButton("保存")
        self.save_bio_button.setObjectName("save_bio_button") # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.save_bio_button.setVisible(False)
        self.save_bio_button.clicked.connect(self.save_bio)
        self.save_bio_button.setProperty("class", "primary_button") # Keep class for QSS
        bio_button_layout.addWidget(self.save_bio_button)

        bio_content_layout.addLayout(bio_button_layout)
        bio_layout.addWidget(bio_content_frame)

        profile_layout.addWidget(bio_container)
        profile_layout.addStretch(1)

    def _set_circular_avatar(self, avatar_data):
        """Loads an image from bytes, makes it circular, and sets it on the avatar_label."""
        pixmap = QPixmap()
        loaded = False
        if avatar_data:
            loaded = pixmap.loadFromData(avatar_data)

        if not loaded:
            logger.warning("Could not load avatar from data. Using default resource.")
            pixmap = QPixmap(":/icons/user.svg")
            if pixmap.isNull():
                 logger.error("Default avatar resource ':/icons/user.svg' is also missing!")
                 pixmap = QPixmap(90, 90)
                 pixmap.fill(Qt.lightGray)

        size = 70  # Reduced size to match the smaller avatar label
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

    @Slot(dict)
    def set_user(self, user):
        """Set the current user and update UI elements, delegating to sub-widgets."""
        logger.info(f"ProfileWidget.set_user called. User is None: {user is None}")
        self.current_user = user

        can_edit = user is not None

        if user:
            logger.debug(f"User data: {user}")
            self.username_label.setText(user.get("username", "N/A"))

            reg_date_str_raw = user.get("registration_date")
            logger.info(f"Raw registration_date from user dict: '{reg_date_str_raw}' (Type: {type(reg_date_str_raw)})" )
            final_display_text = "未知"
            if reg_date_str_raw:
                try:
                    timestamp_part = str(reg_date_str_raw).split('.')[0].split('+')[0].replace('T', ' ')
                    dt_object = datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
                    final_display_text = dt_object.strftime('%Y-%m-%d')
                    logger.info(f"Successfully parsed and formatted date: {final_display_text}")
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Could not parse registration date '{reg_date_str_raw}': {e}. Falling back to '未知'.")
            else:
                logger.warning("registration_date key missing or value is None/empty in user dict. Setting text to '未知'.")
            logger.info(f"Final text to set on reg_date_label: '{final_display_text}'")
            self.reg_date_label.setText(final_display_text)

            bio = user.get("bio", "")
            if bio:
                self.bio_display_label.setText(bio)
                self.bio_edit.setText(bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")
                self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False)

            avatar_data = user.get("avatar")
            self._set_circular_avatar(avatar_data)

        else:
            logger.info("User is None. Resetting profile fields.")
            self.username_label.setText("N/A")
            self.reg_date_label.setText("N/A")
            self.bio_display_label.setText("请先登录")
            self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False)
            self._set_circular_avatar(None)

        self.change_avatar_button.setEnabled(can_edit)
        self.edit_bio_button.setEnabled(can_edit)

        self.stats_achievements_widget.set_user(user)
        self.account_actions_widget.set_user(user)

    @Slot()
    def toggle_bio_edit(self, edit_mode=None):
        """Toggle between displaying and editing the bio."""
        if edit_mode is None:
            currently_editing = self.save_bio_button.isVisible()
            edit_mode = not currently_editing

        can_edit = self.current_user is not None

        self.bio_display_label.setVisible(not edit_mode)
        self.edit_bio_button.setVisible(not edit_mode and can_edit)

        self.bio_edit.setVisible(edit_mode and can_edit)
        self.save_bio_button.setVisible(edit_mode and can_edit)
        self.cancel_bio_button.setVisible(edit_mode and can_edit)

        if not edit_mode:
            current_bio = self.bio_display_label.text()
            if current_bio == "这个人很神秘，什么也没留下..." or current_bio == "请先登录":
                self.bio_edit.setText("")
            else:
                self.bio_edit.setText(current_bio)
        elif can_edit:
            self.bio_edit.setFocus()
            current_bio = self.bio_display_label.text()
            if current_bio != "这个人很神秘，什么也没留下..." and current_bio != "请先登录":
                self.bio_edit.setText(current_bio)
            else:
                self.bio_edit.setText("")

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
            self.user_updated.emit(self.current_user)
        else:
            AnimatedMessageBox.showWarning(self, "失败", "无法保存个人简介，请稍后重试。")

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
                            logger.info(f"Resized avatar to fit within {max_dimension}x{max_dimension} ({len(avatar_bytes)} bytes)")
                        else:
                             logger.info(f"Avatar size is within limits ({len(avatar_bytes)} bytes)")
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
                        self.user_updated.emit(self.current_user)
                    else:
                        AnimatedMessageBox.showWarning(self, "失败", "无法更新数据库中的头像数据。")

                except FileNotFoundError:
                     AnimatedMessageBox.showCritical(self, "错误", f"无法找到文件: {source_path}")
                except Exception as e:
                    logger.error(f"Error changing avatar: {e}")
                    AnimatedMessageBox.showCritical(self, "错误", f"更换头像时发生错误: {e}")

    @Slot()
    def _handle_delete_account(self):
        """Handles the delete account request after confirmation from AccountActionsWidget."""
        if not self.current_user:
            return

        username = self.current_user.get("username", "")
        user_id = self.current_user.get("id")

        password, ok = QInputDialog.getText(
            self,
            "确认注销账号",
            f"请输入您的密码以确认永久删除账号 \"{username}\"：",
            QLineEdit.Password
        )

        if not ok or not password:
            logger.info(f"Account deletion cancelled by user {username} (ID: {user_id}) at password prompt.")
            return

        try:
            success = self.user_manager.delete_user_account(user_id, password)

            if success:
                AnimatedMessageBox.showInformation(self, "账号已注销", f"账号 \"{username}\" 已被永久删除。")
                QTimer.singleShot(10, self.user_logged_out.emit)
            else:
                AnimatedMessageBox.showWarning(self, "注销失败", "密码不正确或发生内部错误，无法注销账号。")
        except Exception as e:
            logger.error(f"Error during account deletion for user {user_id}: {e}")
            AnimatedMessageBox.showCritical(self, "注销出错", f"注销过程中发生意外错误：{e}")
