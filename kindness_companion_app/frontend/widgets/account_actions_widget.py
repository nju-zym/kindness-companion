\
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
                             QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon

# Use correct relative imports with correct filenames
from .animated_message_box import AnimatedMessageBox
from ..password_dialog import PasswordDialog


class AccountActionsWidget(QWidget):
    """
    Widget for handling account actions like password change, logout, delete.
    """
    logout_requested = Signal()
    delete_account_requested = Signal() # Emits when user confirms deletion

    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the action buttons UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins for the main widget layout
        main_layout.setSpacing(15)

        # Create a frame for the action buttons
        action_frame = QFrame()
        action_frame.setObjectName("action_frame")
        action_frame.setStyleSheet("""
            QFrame#action_frame {
                background-color: #202020;
                border: 1px solid #333333;
                border-radius: 16px;
                padding: 10px;
            }
        """)

        # Layout for the frame
        frame_layout = QVBoxLayout(action_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(15)

        # Add a title to the frame
        title_label = QLabel("账户操作")
        title_label.setStyleSheet("font-weight: 600; font-size: 16pt; color: #E67E22;")
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)

        # Create a horizontal layout for the main buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Common button style
        button_style = """
            QPushButton {
                background-color: #2A2A2A;
                color: #F5F5F5;
                border: 1px solid #3A3A3A;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 12pt;
                min-height: 48px; /* Ensure consistent height */
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
            QPushButton:disabled { /* Style for disabled state */
                background-color: #1D1D1D;
                color: #505050;
                border-color: #2A2A2A;
            }
        """

        # Change Password Button
        self.change_password_button = QPushButton("修改密码")
        # 使用文本代替图标，避免SVG加载问题
        self.change_password_button.clicked.connect(self.show_password_dialog)
        self.change_password_button.setStyleSheet(button_style)
        button_layout.addWidget(self.change_password_button)

        # Logout Button
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")
        # 使用文本代替图标，避免SVG加载问题
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setStyleSheet("""
            QPushButton#logout_button {
                background-color: transparent;
                color: #E67E22;
                border: 1px solid #E67E22;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 12pt;
                min-height: 48px;
            }
            QPushButton#logout_button:hover {
                background-color: rgba(230, 126, 34, 0.1);
            }
            QPushButton#logout_button:pressed {
                background-color: rgba(230, 126, 34, 0.2);
            }
            QPushButton#logout_button:disabled {
                background-color: transparent;
                color: #505050;
                border-color: #2A2A2A;
            }
        """)
        button_layout.addWidget(self.logout_button)

        # Add the button layout to the frame
        frame_layout.addLayout(button_layout)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555;")
        separator.setMaximumHeight(1)
        frame_layout.addWidget(separator)

        # Delete Account Button (in its own row)
        self.delete_account_button = QPushButton("注销账号")
        self.delete_account_button.setObjectName("delete_account_button")
        # 使用文本代替图标，避免SVG加载问题
        self.delete_account_button.clicked.connect(self.request_delete_account)
        self.delete_account_button.setStyleSheet("""
            QPushButton#delete_account_button {
                background-color: transparent;
                color: #E74C3C;
                border: 1px solid #E74C3C;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 12pt;
                min-height: 48px;
            }
            QPushButton#delete_account_button:hover {
                background-color: rgba(231, 76, 60, 0.1);
            }
            QPushButton#delete_account_button:pressed {
                background-color: rgba(231, 76, 60, 0.2);
            }
            QPushButton#delete_account_button:disabled {
                background-color: transparent;
                color: #505050;
                border-color: #2A2A2A;
            }
        """)
        frame_layout.addWidget(self.delete_account_button)

        # Add the frame to the main layout
        main_layout.addWidget(action_frame)

        # Initial state: disable buttons if no user
        self.update_button_states(False)

    @Slot(dict)
    def set_user(self, user):
        """Sets the current user and updates button states."""
        self.current_user = user
        self.update_button_states(user is not None)

    def update_button_states(self, enabled):
        """Enable or disable action buttons."""
        self.change_password_button.setEnabled(enabled)
        self.logout_button.setEnabled(enabled)
        self.delete_account_button.setEnabled(enabled)

    @Slot()
    def show_password_dialog(self):
        """Show the change password dialog."""
        if not self.current_user:
            return

        dialog = PasswordDialog(self.user_manager, self.current_user['id'], self)
        if dialog.exec():
            AnimatedMessageBox.showInformation(self, "成功", "密码已成功修改！")

    @Slot()
    def logout(self):
        """Handle user logout request."""
        reply = AnimatedMessageBox.question(
            self,
            "确认退出",
            "您确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            logging.info("User confirmed logout.")
            self.logout_requested.emit() # Emit signal for main window/profile widget to handle

    @Slot()
    def request_delete_account(self):
        """Handle delete account request with confirmation."""
        if not self.current_user:
            return

        username = self.current_user.get('username', '您的账号')
        reply = AnimatedMessageBox.critical(
            self,
            "！！危险操作！！",
            f"您确定要永久删除账号 '{username}' 吗？\n"
            "此操作无法撤销，所有数据将被清除！",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            # Second, more explicit confirmation
            reply_confirm = AnimatedMessageBox.warning(
                self,
                "最后确认",
                f"请再次确认：永久删除账号 '{username}'？",
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply_confirm == QMessageBox.Yes:
                logging.warning(f"User confirmed deletion for account: {username} (ID: {self.current_user.get('id')})")
                # Emit signal instead of directly calling user_manager.delete_user
                self.delete_account_requested.emit()

