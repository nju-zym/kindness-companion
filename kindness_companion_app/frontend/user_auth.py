from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox, QCheckBox, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon


class LoginWidget(QWidget):
    """
    Widget for user login.
    """

    # Signals
    login_successful = Signal(dict)
    register_requested = Signal()

    def __init__(self, user_manager):
        """
        Initialize the login widget.

        Args:
            user_manager: User manager instance
        """
        super().__init__()
        self.user_manager = user_manager
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout - pushes content to the center
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20) # Consistent margins
        self.main_layout.setAlignment(Qt.AlignCenter) # Center content

        # Content container with max width
        content_container = QWidget()
        content_container.setMaximumWidth(450) # Limit max width, same as RegisterWidget
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 30, 15, 30) # Padding inside the container
        content_layout.setSpacing(15) # Spacing between elements

        # Title
        self.title_label = QLabel("欢迎回来")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("请登录您的善行挑战账号")
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.subtitle_label)
        content_layout.addSpacing(15) # Space after subtitle

        # Use QGridLayout for better label/field alignment control
        self.grid_layout = QGridLayout()
        self.grid_layout.setVerticalSpacing(15)
        self.grid_layout.setHorizontalSpacing(10) # Spacing between label and field

        # Username field
        username_label = QLabel("用户名:")
        username_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Align label left
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setMinimumHeight(38) # Reduced height
        self.username_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.grid_layout.addWidget(username_label, 0, 0)
        self.grid_layout.addWidget(self.username_edit, 0, 1)

        # Password field
        password_label = QLabel("密码:")
        password_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Align label left
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setMinimumHeight(38) # Reduced height
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.grid_layout.addWidget(password_label, 1, 0)
        self.grid_layout.addWidget(self.password_edit, 1, 1)

        # Set column stretch: make the input field column (1) expand
        self.grid_layout.setColumnStretch(1, 1)
        # Set label column (0) to take minimum necessary space
        self.grid_layout.setColumnStretch(0, 0)


        content_layout.addLayout(self.grid_layout) # Add the grid layout instead of form layout
        # Removed spacing, handled by container spacing

        icon_size = QSize(16, 16)

        # Login button
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("main_login_button")
        self.login_button.setIcon(QIcon(":/icons/log-in.svg"))
        self.login_button.setIconSize(icon_size)
        self.login_button.setMinimumHeight(35) # Reduced height from 38
        self.login_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Make button expand horizontally
        self.login_button.clicked.connect(self.login)
        content_layout.addWidget(self.login_button) # Add to container layout
        # Adjusted spacing

        # Register link
        self.register_layout = QHBoxLayout()
        self.register_layout.setAlignment(Qt.AlignCenter)
        # Removed margins

        self.register_label = QLabel("还没有账号？")
        self.register_button = QPushButton("立即注册")
        self.register_button.setObjectName("register_button")
        self.register_button.clicked.connect(self.register_requested.emit)

        self.register_layout.addWidget(self.register_label)
        self.register_layout.addWidget(self.register_button)

        content_layout.addLayout(self.register_layout)

        # Add the container to the main layout
        self.main_layout.addWidget(content_container)

        # Set tab order
        self.setTabOrder(self.username_edit, self.password_edit)
        self.setTabOrder(self.password_edit, self.login_button)
        self.setTabOrder(self.login_button, self.register_button)

        # Set focus
        self.username_edit.setFocus()

    def login(self):
        """Attempt to log in with the provided credentials."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username:
            QMessageBox.warning(self, "登录失败", "请输入用户名")
            self.username_edit.setFocus()
            return

        if not password:
            QMessageBox.warning(self, "登录失败", "请输入密码")
            self.password_edit.setFocus()
            return

        user = self.user_manager.login(username, password)

        if user:
            self.login_successful.emit(user)
            self.clear_fields()
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码不正确")
            self.password_edit.clear()
            self.password_edit.setFocus()

    def clear_fields(self):
        """Clear input fields."""
        self.username_edit.clear()
        self.password_edit.clear()


class RegisterWidget(QWidget):
    """
    Widget for user registration.
    """

    # Signals
    register_successful = Signal(dict)
    login_requested = Signal()

    def __init__(self, user_manager):
        """
        Initialize the register widget.

        Args:
            user_manager: User manager instance
        """
        super().__init__()
        self.user_manager = user_manager
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout - pushes content to the center
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20) # Reduced top/bottom margins
        self.main_layout.setAlignment(Qt.AlignCenter) # Center content vertically and horizontally

        # Content container with max width
        content_container = QWidget()
        content_container.setMaximumWidth(450) # Limit max width
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 30, 15, 30) # Padding inside the container
        content_layout.setSpacing(15) # Spacing between elements in the container

        # Title
        self.title_label = QLabel("创建账号")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignCenter) # Center align title
        content_layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("加入善行挑战，开始您的善行之旅")
        self.subtitle_label.setObjectName("subtitle_label")
        self.subtitle_label.setAlignment(Qt.AlignCenter) # Center align subtitle
        content_layout.addWidget(self.subtitle_label)
        content_layout.addSpacing(15) # Space after subtitle

        # Form layout
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignRight)
        # Removed contents margins from form, handled by container
        self.form_layout.setVerticalSpacing(15) # Adjusted vertical spacing
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow) # Ensure fields expand horizontally
        self.form_layout.setFormAlignment(Qt.AlignCenter) # Center the form content

        # Username field
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setMinimumHeight(38) # Reduced height
        self.username_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Use Fixed height
        self.form_layout.addRow("用户名:", self.username_edit)

        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setMinimumHeight(38) # Reduced height
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Use Fixed height
        self.form_layout.addRow("密码:", self.password_edit)

        # Confirm password field
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("请再次输入密码")
        self.confirm_password_edit.setMinimumHeight(38) # Reduced height
        self.confirm_password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Use Fixed height
        self.form_layout.addRow("确认密码:", self.confirm_password_edit)

        content_layout.addLayout(self.form_layout)
        # Removed spacing here, handled by container spacing

        icon_size = QSize(16, 16)

        # Terms and conditions
        self.terms_layout = QHBoxLayout()
        self.terms_layout.setAlignment(Qt.AlignCenter)
        # Removed margins, handled by container spacing

        self.terms_checkbox = QCheckBox("我已阅读并同意")
        self.terms_button = QPushButton("用户协议")
        self.terms_button.setObjectName("terms_button")
        self.terms_button.clicked.connect(self.show_terms)

        self.terms_layout.addWidget(self.terms_checkbox)
        self.terms_layout.addWidget(self.terms_button)

        content_layout.addLayout(self.terms_layout)
        # Adjusted spacing before register button via container spacing

        # Register button
        self.register_button = QPushButton("注册")
        self.register_button.setObjectName("main_register_button")
        self.register_button.setIcon(QIcon(":/icons/user-plus.svg"))
        self.register_button.setIconSize(icon_size)
        self.register_button.setMinimumHeight(35) # Reduced height from 38
        self.register_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Expand horizontally
        self.register_button.clicked.connect(self.register)
        content_layout.addWidget(self.register_button) # Add directly to container layout
        # Adjusted spacing before login link via container spacing

        # Login link
        self.login_layout = QHBoxLayout()
        self.login_layout.setAlignment(Qt.AlignCenter)
        # Removed margins

        self.login_label = QLabel("已有账号？")
        self.login_button = QPushButton("返回登录")
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.login_requested.emit)

        self.login_layout.addWidget(self.login_label)
        self.login_layout.addWidget(self.login_button)

        content_layout.addLayout(self.login_layout)

        # Add the container to the main layout
        self.main_layout.addWidget(content_container)

        # Set tab order (remains the same)
        self.setTabOrder(self.username_edit, self.password_edit)
        self.setTabOrder(self.password_edit, self.confirm_password_edit)
        self.setTabOrder(self.confirm_password_edit, self.terms_checkbox)
        self.setTabOrder(self.terms_checkbox, self.register_button)
        self.setTabOrder(self.register_button, self.login_button)

        # Set focus
        self.username_edit.setFocus()

    def register(self):
        """Attempt to register with the provided information."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        # Validate input
        if not username:
            QMessageBox.warning(self, "注册失败", "请输入用户名")
            self.username_edit.setFocus()
            return

        if not password:
            QMessageBox.warning(self, "注册失败", "请输入密码")
            self.password_edit.setFocus()
            return

        if password != confirm_password:
            QMessageBox.warning(self, "注册失败", "两次输入的密码不一致")
            self.confirm_password_edit.clear()
            self.confirm_password_edit.setFocus()
            return

        if not self.terms_checkbox.isChecked():
            QMessageBox.warning(self, "注册失败", "请阅读并同意用户协议")
            self.terms_checkbox.setFocus()
            return

        # Corrected user registration call
        user = self.user_manager.register_user(username, password)

        if user:
            self.register_successful.emit(user)
            self.clear_fields()
        else:
            QMessageBox.warning(self, "注册失败", "用户名已存在，请选择其他用户名")
            self.username_edit.setFocus()

    def show_terms(self):
        """Show terms and conditions."""
        QMessageBox.information(
            self,
            "用户协议",
            "善行挑战应用用户协议\n\n"
            "1. 本应用旨在鼓励用户进行善行，提升社会正能量。\n"
            "2. 用户需对自己的行为负责，不得利用本应用进行违法或不道德活动。\n"
            "3. 用户提供的个人信息将被安全保存，不会泄露给第三方。\n"
            "4. 本应用保留随时修改服务内容和协议的权利。\n\n"
            "感谢您的理解与支持！"
        )

    def clear_fields(self):
        """Clear input fields."""
        self.username_edit.clear()
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.terms_checkbox.setChecked(False)
