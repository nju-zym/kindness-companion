import logging # Add logging import
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QMessageBox, QButtonGroup, QSizePolicy
)
# QTimer might not be needed here anymore, but keep it for now
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QFontMetrics

from .user_auth import LoginWidget, RegisterWidget
from .challenge_ui import ChallengeListWidget
from .checkin_ui import CheckinWidget
from .progress_ui import ProgressWidget
from .reminder_ui import ReminderWidget
from .profile_ui import ProfileWidget
from .community_ui import CommunityWidget


class MainWindow(QMainWindow):
    """
    Main application window with navigation and content areas.
    """

    # Signal to notify when user logs in or out
    user_changed = Signal(dict)

    def __init__(self, user_manager, challenge_manager, progress_tracker, reminder_scheduler):
        """
        Initialize the main window.

        Args:
            user_manager: User manager instance
            challenge_manager: Challenge manager instance
            progress_tracker: Progress tracker instance
            reminder_scheduler: Reminder scheduler instance
        """
        super().__init__()

        # Store backend managers
        self.user_manager = user_manager
        self.challenge_manager = challenge_manager
        self.progress_tracker = progress_tracker
        self.reminder_scheduler = reminder_scheduler

        # Set up reminder callback
        self.reminder_scheduler.set_callback(self.show_reminder)

        # Set window properties
        self.setWindowTitle("善行挑战 (Kindness Challenge)")
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        # Create navigation sidebar
        self.setup_navigation()

        # Create content area
        self.setup_content_area()

        # Connect signals
        self.connect_signals()

        # Start with login screen
        self.show_login()

    def setup_navigation(self):
        """Set up the navigation sidebar."""
        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("nav_widget")  # Set object name for styling
        self.nav_widget.setMinimumWidth(200)  # 确保侧边栏有足够宽度

        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setAlignment(Qt.AlignTop)
        self.nav_layout.setContentsMargins(5, 15, 5, 10)  # 调整侧边栏内边距

        # 创建一个容器控件来包含标题标签
        self.title_container = QWidget()
        self.title_container.setMinimumHeight(70)  # 确保容器有足够的高度
        self.title_layout = QVBoxLayout(self.title_container)
        self.title_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        self.title_layout.setAlignment(Qt.AlignCenter)

        # App title
        self.title_label = QLabel("善行挑战")
        self.title_label.setObjectName("title_label")  # Set object name
        self.title_label.setAlignment(Qt.AlignCenter)

        # 设置字体并显式指定大小
        title_font = QFont("Hiragino Sans GB", 20, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setMinimumHeight(40)  # 固定高度
        self.title_label.setStyleSheet("padding: 0px; margin: 0px;")  # 覆盖样式表中的内边距

        # 添加标题到容器并显式设置大小策略
        self.title_layout.addWidget(self.title_label)
        self.title_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 添加标题容器到导航布局
        self.nav_layout.addWidget(self.title_container)
        self.nav_layout.addSpacing(10)  # 在标题下方添加额外空间

        # Navigation buttons
        self.nav_buttons = {}
        self.nav_button_group = QButtonGroup(self)  # Use QButtonGroup for exclusive selection
        self.nav_button_group.setExclusive(True)

        # Define navigation items with icons
        nav_items = [
            ("challenges", "挑战列表", self.show_challenges, ":/icons/list.svg"),
            ("checkin", "每日打卡", self.show_checkin, ":/icons/check-square.svg"),
            ("progress", "我的进度", self.show_progress, ":/icons/calendar-check.svg"),
            ("reminders", "提醒设置", self.show_reminders, ":/icons/bell.svg"),
            ("community", "善意墙", self.show_community, ":/icons/users.svg"),
            ("profile", "个人信息", self.show_profile, ":/icons/user.svg"),
        ]

        icon_size = QSize(18, 18)  # Define a standard icon size

        for item_id, label, callback, icon_path in nav_items:
            button = QPushButton(label)
            if icon_path:
                try:
                    icon = QIcon(icon_path)
                    if icon.isNull():
                        print(f"Warning: Icon not found at {icon_path}")
                    button.setIcon(icon)
                    button.setIconSize(icon_size)
                except Exception as e:
                    print(f"Error loading icon {icon_path}: {e}")

            button.setCheckable(True)  # Make buttons checkable
            button.clicked.connect(callback)
            button.clicked.connect(lambda checked=False, b=button: self.update_button_style(b))
            self.nav_buttons[item_id] = button
            self.nav_button_group.addButton(button)  # Add to group
            self.nav_layout.addWidget(button)
            button.setEnabled(False)  # Disabled until login

        # Add stretch to push logout button to bottom
        self.nav_layout.addStretch()

        # Add navigation to main layout
        self.main_layout.addWidget(self.nav_widget, 1)

    def setup_content_area(self):
        """Set up the content area with stacked widget."""
        self.content_widget = QStackedWidget()

        # Create pages
        self.login_widget = LoginWidget(self.user_manager)
        self.register_widget = RegisterWidget(self.user_manager)
        self.challenge_widget = ChallengeListWidget(self.challenge_manager, self.progress_tracker)
        self.checkin_widget = CheckinWidget(self.progress_tracker, self.challenge_manager)
        self.progress_widget = ProgressWidget(self.progress_tracker, self.challenge_manager)
        self.reminder_widget = ReminderWidget(self.reminder_scheduler, self.challenge_manager)
        self.community_widget = CommunityWidget()
        self.profile_widget = ProfileWidget(self.user_manager, self.progress_tracker, self.challenge_manager)

        # Add pages to stacked widget
        self.content_widget.addWidget(self.login_widget)
        self.content_widget.addWidget(self.register_widget)
        self.content_widget.addWidget(self.challenge_widget)
        self.content_widget.addWidget(self.checkin_widget)
        self.content_widget.addWidget(self.progress_widget)
        self.content_widget.addWidget(self.reminder_widget)
        self.content_widget.addWidget(self.community_widget)
        self.content_widget.addWidget(self.profile_widget)

        # Add content to main layout
        self.main_layout.addWidget(self.content_widget, 4)

    def connect_signals(self):
        """Connect signals between widgets."""
        # Connect login signals
        self.login_widget.login_successful.connect(self.on_login_successful)
        self.login_widget.register_requested.connect(self.show_register)

        # Connect register signals
        self.register_widget.register_successful.connect(self.on_register_successful)
        self.register_widget.login_requested.connect(self.show_login)

        # Connect user_changed signal to widgets
        self.user_changed.connect(self.challenge_widget.set_user)
        self.user_changed.connect(self.checkin_widget.set_user)
        self.user_changed.connect(self.progress_widget.set_user)
        self.user_changed.connect(self.reminder_widget.set_user)
        self.user_changed.connect(self.community_widget.set_user)
        self.user_changed.connect(self.profile_widget.set_user)

        # Connect profile widget signals
        self.profile_widget.user_updated.connect(self.update_user_info)
        self.profile_widget.user_logged_out.connect(self.handle_logout)

    @Slot(dict)
    def on_login_successful(self, user):
        """
        Handle successful login.

        Args:
            user (dict): User information
        """
        logging.info("Login successful, preparing UI updates...")
        # Enable navigation buttons
        for button in self.nav_buttons.values():
            button.setEnabled(True)
            button.style().unpolish(button)
            button.style().polish(button)

        # Emit user_changed signal
        self.user_changed.emit(user)

        # Show challenges page and set its button as checked
        logging.info("Calling show_challenges...")
        self.show_challenges()
        logging.info("Returned from show_challenges.")

        if "challenges" in self.nav_buttons:
             self.nav_buttons["challenges"].setChecked(True)
             self.update_button_style(self.nav_buttons["challenges"])

        # Show a non-modal welcome message
        # Create an instance of QMessageBox
        welcome_msg = QMessageBox(self) # Set parent to main window
        welcome_msg.setWindowTitle("登录成功")
        welcome_msg.setText(f"欢迎回来，{user['username']}！\n准备好今天的善行挑战了吗？")
        welcome_msg.setIcon(QMessageBox.Information)
        # Make it non-modal
        welcome_msg.setWindowModality(Qt.NonModal)
        # Ensure it's deleted when closed
        welcome_msg.setAttribute(Qt.WA_DeleteOnClose)
        # Show the message box (does not block)
        welcome_msg.show()
        logging.info("Non-modal welcome message shown.")


    @Slot(dict)
    def on_register_successful(self, user):
        """
        Handle successful registration.

        Args:
            user (dict): User information
        """
        # Show login page
        self.show_login()

        # Show success message
        QMessageBox.information(
            self,
            "注册成功",
            f"欢迎加入善行挑战，{user['username']}！\n请使用您的新账号登录。"
        )

    def logout(self):
        """Log out the current user."""
        self.user_manager.logout()

        # Disable navigation buttons
        for button in self.nav_buttons.values():
            button.setEnabled(False)
            button.style().unpolish(button)
            button.style().polish(button)

        # Uncheck all nav buttons
        checked_button = self.nav_button_group.checkedButton()
        if checked_button:
            self.nav_button_group.setExclusive(False)
            checked_button.setChecked(False)
            self.nav_button_group.setExclusive(True)
            self.update_button_style(checked_button)

        # Emit user_changed signal with None
        self.user_changed.emit(None)

        # Show login page
        self.show_login()

    def show_login(self):
        """Show the login page."""
        self.content_widget.setCurrentWidget(self.login_widget)

    def show_register(self):
        """Show the registration page."""
        self.content_widget.setCurrentWidget(self.register_widget)

    def show_challenges(self):
        """Show the challenges page."""
        logging.info(f"Attempting to switch to challenge_widget. Current widget: {self.content_widget.currentWidget()}")
        self.content_widget.setCurrentWidget(self.challenge_widget)
        logging.info(f"Switched content widget. Current widget is now: {self.content_widget.currentWidget()}")

    def show_checkin(self):
        """Show the check-in page."""
        self.content_widget.setCurrentWidget(self.checkin_widget)

    def show_progress(self):
        """Show the progress page."""
        self.content_widget.setCurrentWidget(self.progress_widget)

    def show_reminders(self):
        """Show the reminders page."""
        self.content_widget.setCurrentWidget(self.reminder_widget)

    def show_community(self):
        """Show the community page."""
        self.content_widget.setCurrentWidget(self.community_widget)

    def show_profile(self):
        """Show the profile page."""
        self.content_widget.setCurrentWidget(self.profile_widget)

    def show_reminder(self, reminder):
        """
        Show a reminder notification.

        Args:
            reminder (dict): Reminder information
        """
        QMessageBox.information(
            self,
            "善行提醒",
            f"别忘了今天的善行挑战：\n{reminder['challenge_title']}"
        )

    def update_button_style(self, clicked_button=None):
        """Updates the style of navigation buttons based on the checked state."""
        for item_id, button in self.nav_buttons.items():
            is_checked = (button == clicked_button and button.isCheckable() and button.isChecked())
            button.setProperty("selected", is_checked)
            button.style().unpolish(button)
            button.style().polish(button)

    def update_user_info(self, user_info):
        """
        Update user information in the application.

        Args:
            user_info (dict): Updated user information
        """
        self.user_changed.emit(user_info)

    def handle_logout(self):
        """Handle logout triggered from the profile widget."""
        self.logout()
