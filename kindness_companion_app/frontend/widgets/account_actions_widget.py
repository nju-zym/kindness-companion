import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QMessageBox,
    QSizePolicy,
)
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
    delete_account_requested = Signal()  # Emits when user confirms deletion

    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the action buttons UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # No margins for the main widget layout
        main_layout.setSpacing(15)

        # Create a frame for the action buttons
        action_frame = QFrame()
        action_frame.setObjectName("action_frame")  # Keep object name

        # Layout for the frame
        frame_layout = QVBoxLayout(action_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(15)

        # Add a title to the frame
        title_label = QLabel("账户操作")
        title_label.setObjectName("account_actions_title")  # Add object name
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title_label)

        # Create a horizontal layout for the main buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Change Password Button
        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setObjectName(
            "change_password_button"
        )  # Add object name
        # 使用文本代替图标，避免SVG加载问题
        self.change_password_button.clicked.connect(self.show_password_dialog)
        button_layout.addWidget(self.change_password_button)

        # Logout Button
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")  # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.logout_button.clicked.connect(self.logout)
        button_layout.addWidget(self.logout_button)

        # Add the button layout to the frame
        frame_layout.addLayout(button_layout)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("account_actions_separator")  # Add object name
        separator.setMaximumHeight(1)
        frame_layout.addWidget(separator)

        # Delete Account Button (in its own row)
        self.delete_account_button = QPushButton("注销账号")
        self.delete_account_button.setObjectName(
            "delete_account_button"
        )  # Keep object name
        # 使用文本代替图标，避免SVG加载问题
        self.delete_account_button.clicked.connect(self.request_delete_account)
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

        dialog = PasswordDialog(self.user_manager, self.current_user["id"], self)
        if dialog.exec():
            AnimatedMessageBox.showInformation(
                self.window(), "成功", "密码已成功修改！"
            )

    @Slot()
    def logout(self):
        """Handle user logout request."""
        reply = AnimatedMessageBox.question(
            self.window(),
            "确认退出",
            "您确定要退出登录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User confirmed logout.")
            self.logout_requested.emit()  # Emit signal for main window/profile widget to handle

    @Slot()
    def request_delete_account(self):
        """Handle delete account request with confirmation."""
        if not self.current_user:
            return

        username = self.current_user.get("username", "您的账号")
        reply = AnimatedMessageBox.critical(
            self.window(),
            "！！危险操作！！",
            f"您确定要永久删除账号 '{username}' 吗？\n"
            "此操作无法撤销，所有数据将被清除！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Second, more explicit confirmation
            reply_confirm = AnimatedMessageBox.warning(
                self.window(),
                "最后确认",
                f"请再次确认：永久删除账号 '{username}'？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if reply_confirm == QMessageBox.StandardButton.Yes:
                logging.warning(
                    f"User confirmed deletion for account: {username} (ID: {self.current_user.get('id')})"
                )
                # Emit signal instead of directly calling user_manager.delete_user
                self.delete_account_requested.emit()
