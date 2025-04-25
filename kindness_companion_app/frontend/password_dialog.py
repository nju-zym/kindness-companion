from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget, QSizePolicy, QHBoxLayout, QDialogButtonBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint # Removed animation imports
from PySide6.QtGui import QIcon, QScreen

# Import the new BaseDialog
from .widgets.base_dialog import BaseDialog
# Import AnimatedMessageBox
from .widgets.animated_message_box import AnimatedMessageBox

# Change inheritance from QDialog to BaseDialog
class PasswordDialog(BaseDialog):
    """
    对话框用于修改用户密码, 继承自 BaseDialog 以获得居中和动画效果。
    """
    # 定义信号
    password_changed = Signal(dict)

    def __init__(self, user_manager, current_user, parent=None):
        """
        初始化密码修改对话框

        Args:
            user_manager: 用户管理器实例
            current_user: 当前用户信息
            parent: 父窗口
        """
        # Call BaseDialog's __init__
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = current_user

        self.setWindowTitle("修改密码")
        self.setMinimumWidth(450)
        # Modality is handled by BaseDialog

        # --- Animation Setup removed, handled by BaseDialog ---

        self.setup_ui()

    # --- Animation Methods removed, handled by BaseDialog ---
    # showEvent, closeEvent, accept, reject, _handle_animation_finished are inherited

    def setup_ui(self):
        """设置用户界面"""
        # --- Main Layout for the Dialog ---
        dialog_layout = QVBoxLayout(self) # Set layout directly on the dialog
        dialog_layout.setContentsMargins(30, 30, 30, 30)
        dialog_layout.setSpacing(20)
        dialog_layout.setAlignment(Qt.AlignCenter)

        # --- Content Container ---
        content_widget = QWidget()
        content_widget.setMaximumWidth(400)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(25)

        # --- Form Layout ---
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(10)

        # Labels
        current_pwd_label = QLabel("当前密码:")
        current_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        new_pwd_label = QLabel("新密码:")
        new_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        confirm_pwd_label = QLabel("确认新密码:")
        confirm_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Helper to create styled password fields
        def create_password_field(placeholder):
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(placeholder)
            edit.setMinimumHeight(38)
            edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            return edit

        self.current_password_edit = create_password_field("请输入当前密码")
        self.new_password_edit = create_password_field("请输入新密码")
        self.confirm_password_edit = create_password_field("请再次输入新密码")

        # Add widgets to form layout
        form_layout.addWidget(current_pwd_label, 0, 0)
        form_layout.addWidget(self.current_password_edit, 0, 1)
        form_layout.addWidget(new_pwd_label, 1, 0)
        form_layout.addWidget(self.new_password_edit, 1, 1)
        form_layout.addWidget(confirm_pwd_label, 2, 0)
        form_layout.addWidget(self.confirm_password_edit, 2, 1)

        form_layout.setColumnStretch(1, 1)

        content_layout.addLayout(form_layout)

        # --- Button Layout ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch(1)

        self.save_button = QPushButton("保存修改")
        self.save_button.setObjectName("save_button")
        self.save_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_button.setIconSize(QSize(16, 16))
        self.save_button.setMinimumHeight(40)
        self.save_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.save_button.clicked.connect(self.save_password)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # Connect cancel button to reject() which now triggers animated close via BaseDialog
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch(1)

        content_layout.addLayout(button_layout)

        # Add the content container to the main dialog layout
        dialog_layout.addWidget(content_widget)

        # Set initial focus
        self.current_password_edit.setFocus()


    def save_password(self):
        """保存密码修改"""
        if not self.current_user:
            self.reject()
            return

        # 获取输入值
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        # 验证密码输入
        if not current_password:
            # Use AnimatedMessageBox
            AnimatedMessageBox.showWarning(self, "保存失败", "请输入当前密码")
            self.current_password_edit.setFocus() # Set focus back
            return

        if not new_password:
            # Use AnimatedMessageBox
            AnimatedMessageBox.showWarning(self, "保存失败", "请输入新密码")
            self.new_password_edit.setFocus() # Set focus back
            return

        if len(new_password) < 6: # Example: Add minimum length check
             # Use AnimatedMessageBox
             AnimatedMessageBox.showWarning(self, "保存失败", "新密码长度至少需要6位")
             self.new_password_edit.setFocus()
             return

        if new_password != confirm_password:
            # Use AnimatedMessageBox
            AnimatedMessageBox.showWarning(self, "保存失败", "两次输入的新密码不一致")
            self.confirm_password_edit.clear()
            self.confirm_password_edit.setFocus() # Set focus back
            return

        # 验证当前密码
        user = self.user_manager.login(
            self.current_user["username"],
            current_password
        )

        if not user:
            # Use AnimatedMessageBox
            AnimatedMessageBox.showWarning(self, "保存失败", "当前密码不正确")
            self.current_password_edit.clear() # Clear incorrect password
            self.current_password_edit.setFocus() # Set focus back
            return

        # 更新用户密码 (Assume update_profile takes id and new_password)
        # Make sure user_manager.update_profile handles password hashing correctly
        success = self.user_manager.update_profile(
            self.current_user["id"],
            new_password=new_password # Pass as keyword argument if necessary
        )

        if success:
            # 清空密码字段
            self.current_password_edit.clear()
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()

            # Show success message using AnimatedMessageBox
            # Pass self as parent for the message box
            AnimatedMessageBox.showInformation(self, "成功", "密码已成功修改！")

            # Emit signal
            updated_user = self.user_manager.get_user_by_id(self.current_user["id"])
            if updated_user:
                self.password_changed.emit(updated_user)

            # Accept the dialog (triggers animated close via BaseDialog)
            self.accept()
        else:
            # Show error message using AnimatedMessageBox
            AnimatedMessageBox.showWarning(self, "保存失败", "密码修改失败，请稍后重试")
            # Do not close the dialog on failure