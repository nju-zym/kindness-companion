from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon


class PasswordDialog(QDialog):
    """
    对话框用于修改用户密码
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
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = current_user

        self.setWindowTitle("修改密码")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        self.setWindowModality(Qt.ApplicationModal)  # 应用模态，阻止与其他窗口交互

        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # 表单布局
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(20)
        form_layout.setHorizontalSpacing(15)

        # 创建标签和输入框
        current_pwd_label = QLabel("当前密码:")
        current_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        new_pwd_label = QLabel("新密码:")
        new_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        confirm_pwd_label = QLabel("确认新密码:")
        confirm_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 创建密码输入框的通用函数
        def create_password_field(placeholder):
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(placeholder)
            edit.setFixedHeight(35)  # 适当的输入框高度
            edit.setTextMargins(8, 0, 8, 0)  # 左上右下文本边距
            return edit

        # 创建三个密码输入框
        self.current_password_edit = create_password_field("请输入当前密码")
        self.new_password_edit = create_password_field("请输入新密码")
        self.confirm_password_edit = create_password_field("请再次输入新密码")

        # 添加到布局中
        form_layout.addWidget(current_pwd_label, 0, 0)
        form_layout.addWidget(self.current_password_edit, 0, 1)
        form_layout.addWidget(new_pwd_label, 1, 0)
        form_layout.addWidget(self.new_password_edit, 1, 1)
        form_layout.addWidget(confirm_pwd_label, 2, 0)
        form_layout.addWidget(self.confirm_password_edit, 2, 1)

        # 设置列宽度比例
        form_layout.setColumnMinimumWidth(0, 100)  # 为标签列设置最小宽度
        form_layout.setColumnStretch(0, 1)  # 标签列占比
        form_layout.setColumnStretch(1, 3)  # 输入框列占比更多

        main_layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QGridLayout()
        button_layout.setHorizontalSpacing(15)

        # 保存按钮
        self.save_button = QPushButton("保存修改")
        self.save_button.setObjectName("save_button")  # 设置对象名称用于样式
        self.save_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_button.setIconSize(QSize(16, 16))
        self.save_button.setMinimumHeight(40)  # 按钮高度
        self.save_button.clicked.connect(self.save_password)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancel_button")  # 设置对象名称用于样式
        self.cancel_button.setMinimumHeight(40)  # 按钮高度
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.cancel_button, 0, 0)
        button_layout.addWidget(self.save_button, 0, 1)

        main_layout.addLayout(button_layout)

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
            QMessageBox.warning(
                self,
                "保存失败",
                "请输入当前密码"
            )
            return

        if not new_password:
            QMessageBox.warning(
                self,
                "保存失败",
                "请输入新密码"
            )
            return

        if new_password != confirm_password:
            QMessageBox.warning(
                self,
                "保存失败",
                "两次输入的新密码不一致"
            )
            return

        # 验证当前密码
        user = self.user_manager.login(
            self.current_user["username"],
            current_password
        )

        if not user:
            QMessageBox.warning(
                self,
                "保存失败",
                "当前密码不正确"
            )
            return

        # 更新用户密码
        success = self.user_manager.update_profile(
            self.current_user["id"],
            new_password
        )

        if success:
            # 清空密码字段
            self.current_password_edit.clear()
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()

            QMessageBox.information(self, "成功", "密码已成功修改！")

            # 获取更新后的用户信息
            updated_user = self.user_manager.get_user_by_id(self.current_user["id"])
            if updated_user:
                self.password_changed.emit(updated_user)  # 发送信号

            self.accept()  # 关闭对话框
        else:
            QMessageBox.warning(
                self,
                "保存失败",
                "密码修改失败，请稍后重试"
            )