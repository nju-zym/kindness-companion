from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QMessageBox, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QFont

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

        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setAlignment(Qt.AlignTop)

        # App title
        self.title_label = QLabel("善行挑战")
        self.title_label.setObjectName("title_label")  # Set object name
        self.title_label.setAlignment(Qt.AlignCenter)
        self.nav_layout.addWidget(self.title_label)

        # Navigation buttons
        self.nav_buttons = {}
        self.nav_button_group = QButtonGroup(self)  # Use QButtonGroup for exclusive selection
        self.nav_button_group.setExclusive(True)

        # Define navigation items with icons
        nav_items = [
            ("challenges", "挑战列表", self.show_challenges, "kindness_challenge_app/resources/icons/list.svg"),
            ("checkin", "每日打卡", self.show_checkin, "kindness_challenge_app/resources/icons/check-square.svg"),
            ("progress", "我的进度", self.show_progress, "kindness_challenge_app/resources/icons/calendar-check.svg"),
            ("reminders", "提醒设置", self.show_reminders, "kindness_challenge_app/resources/icons/bell.svg"),
            ("community", "善意墙", self.show_community, "kindness_challenge_app/resources/icons/users.svg"),
            ("profile", "个人信息", self.show_profile, "kindness_challenge_app/resources/icons/user.svg"),
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

        # Logout button (initially hidden)
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")  # Set object name
        self.logout_button.setIcon(QIcon("kindness_challenge_app/resources/icons/log-out.svg"))  # Add icon
        self.logout_button.setIconSize(icon_size)  # Use standard size
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setVisible(False)
        self.nav_layout.addWidget(self.logout_button)

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
        # Enable navigation buttons
        for button in self.nav_buttons.values():
            button.setEnabled(True)
            button.style().unpolish(button)
            button.style().polish(button)

        # Show logout button
        self.logout_button.setVisible(True)

        # Emit user_changed signal
        self.user_changed.emit(user)

        # Show challenges page and set its button as checked
        self.show_challenges()
        if "challenges" in self.nav_buttons:
            self.nav_buttons["challenges"].setChecked(True)
            self.update_button_style(self.nav_buttons["challenges"])

        # Show welcome message
        QMessageBox.information(
            self,
            "登录成功",
            f"欢迎回来，{user['username']}！\n准备好今天的善行挑战了吗？"
        )

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

        # Hide logout button
        self.logout_button.setVisible(False)

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
        self.content_widget.setCurrentWidget(self.challenge_widget)

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
