from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget # Add QWidget here
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox

# Change inheritance from QDialog to AnimatedMessageBox
class PasswordDialog(AnimatedMessageBox):
    """
    对话框用于修改用户密码, 继承自 AnimatedMessageBox 以获得动画效果。
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
        # Call AnimatedMessageBox's __init__
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = current_user

        # Set properties previously set on QDialog
        self.setWindowTitle("修改密码")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        # AnimatedMessageBox handles modality differently, exec() makes it modal
        # self.setWindowModality(Qt.ApplicationModal) # Not needed when using exec()

        # Keep internal message box type as Information for success message
        self.setIcon(QMessageBox.Information) # Set default icon (can be overridden)

        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        # Main layout - AnimatedMessageBox already has a layout, add to it?
        # Let's create a main widget and set *its* layout, then add it.
        # Or, more simply, reuse the existing layout structure but apply it to 'self'.
        # QMessageBox has its own internal layout. We need to add our widgets carefully.
        # Let's create a container widget for our custom form elements.

        container_widget = QWidget()
        main_layout = QVBoxLayout(container_widget) # Layout for our custom content
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # --- Form Layout ---
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(20)
        form_layout.setHorizontalSpacing(15)

        current_pwd_label = QLabel("当前密码:")
        current_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        new_pwd_label = QLabel("新密码:")
        new_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        confirm_pwd_label = QLabel("确认新密码:")
        confirm_pwd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def create_password_field(placeholder):
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(placeholder)
            edit.setFixedHeight(35)
            edit.setTextMargins(8, 0, 8, 0)
            return edit

        self.current_password_edit = create_password_field("请输入当前密码")
        self.new_password_edit = create_password_field("请输入新密码")
        self.confirm_password_edit = create_password_field("请再次输入新密码")

        form_layout.addWidget(current_pwd_label, 0, 0)
        form_layout.addWidget(self.current_password_edit, 0, 1)
        form_layout.addWidget(new_pwd_label, 1, 0)
        form_layout.addWidget(self.new_password_edit, 1, 1)
        form_layout.addWidget(confirm_pwd_label, 2, 0)
        form_layout.addWidget(self.confirm_password_edit, 2, 1)

        form_layout.setColumnMinimumWidth(0, 100)
        form_layout.setColumnStretch(0, 1)
        form_layout.setColumnStretch(1, 3)

        main_layout.addLayout(form_layout)

        # --- Button Layout ---
        button_layout = QGridLayout()
        button_layout.setHorizontalSpacing(15)

        self.save_button = QPushButton("保存修改")
        self.save_button.setObjectName("save_button")
        self.save_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_button.setIconSize(QSize(16, 16))
        self.save_button.setMinimumHeight(40)
        # Connect save_button to save_password, which now might call accept() or show another message box
        self.save_button.clicked.connect(self.save_password)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setMinimumHeight(40)
        # Connect cancel_button to reject() to close the dialog
        self.cancel_button.clicked.connect(self.reject) # reject() will trigger closeEvent animation

        button_layout.addWidget(self.cancel_button, 0, 0)
        button_layout.addWidget(self.save_button, 0, 1)

        main_layout.addLayout(button_layout)

        # --- Add container to QMessageBox layout ---
        # QMessageBox layout is complex. A common way is to add a widget to the button box layout
        # or replace the label. Let's try adding it to the main layout provided by QMessageBox.
        # Accessing the layout directly is fragile. Let's add the container widget using addWidget.
        # We might need to remove the default label/text area first.
        self.setText("") # Clear default text area
        # Find the layout of the QMessageBox and add our container
        # This is hacky and might break with Qt updates.
        try:
            # Attempt to find the main layout (often a QGridLayout)
            qmbox_layout = self.layout()
            if qmbox_layout:
                 # Add our container widget. Index might need adjustment.
                 # Let's assume adding it as the first element in the main area is desired.
                 # QMessageBox structure: Icon | Label/Text | ButtonBox
                 # Try inserting into the grid layout if possible
                 if isinstance(qmbox_layout, QGridLayout):
                     # Span across columns, insert at row 0 or 1 depending on icon/label presence
                     # Let's try adding it at row 1, spanning 2 columns (index 1, 1)
                     qmbox_layout.addWidget(container_widget, 1, 1, 1, 1) # Adjust row/col/span as needed
                 else:
                     # Fallback for other layouts (e.g., QVBoxLayout)
                     qmbox_layout.insertWidget(0, container_widget) # Insert at the top
            else:
                 # Fallback if layout() returns None (shouldn't happen for QMessageBox)
                 self.setLayout(main_layout) # Set our layout directly (might lose QMessageBox structure)
                 print("Warning: Could not access QMessageBox layout, setting layout directly.")

        except Exception as e:
            print(f"Error adding custom widget to QMessageBox layout: {e}")
            # Fallback: Just set the layout on the dialog directly
            self.setLayout(main_layout)


        # Remove standard buttons provided by QMessageBox, we have our own Save/Cancel
        self.setStandardButtons(QMessageBox.NoButton)


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
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "保存失败",
                "请输入当前密码"
            )
            return

        if not new_password:
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "保存失败",
                "请输入新密码"
            )
            return

        if new_password != confirm_password:
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
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
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
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

            # Show a *separate* success message box
            AnimatedMessageBox.showInformation(self.parent(), "成功", "密码已成功修改！") # Show relative to parent

            # Emit signal
            updated_user = self.user_manager.get_user_by_id(self.current_user["id"])
            if updated_user:
                self.password_changed.emit(updated_user)

            # Accept the dialog (triggers closeEvent animation)
            self.accept()
        else:
            # Show a *separate* error message box
            AnimatedMessageBox.showWarning(
                self, # Show relative to this dialog
                "保存失败",
                "密码修改失败，请稍后重试"
            )
            # Do not close the dialog on failure

    # Inherits showEvent and closeEvent from AnimatedMessageBox for animations