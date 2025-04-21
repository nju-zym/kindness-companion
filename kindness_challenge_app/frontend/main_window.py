from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QMessageBox, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QFont

from .user_auth import LoginWidget, RegisterWidget
from .challenge_ui import ChallengeListWidget
from .progress_ui import ProgressWidget
from .reminder_ui import ReminderWidget
from .profile_ui import ProfileWidget


# Stylesheet for the navigation bar
NAV_STYLESHEET = """
QWidget#nav_widget { /* Target the navigation widget specifically */
    background-color: #e9ecef; /* Light gray background */
    border-right: 1px solid #ced4da; /* Subtle border */
}

QLabel#title_label {
    font-size: 20pt; /* Adjusted title size */
    font-weight: bold;
    color: #343a40; /* Dark gray */
    padding: 15px 0; /* Add padding */
    margin-bottom: 15px; /* Add margin below title */
    font-family: "Helvetica Neue", Arial, sans-serif; /* Ensure font family */
}

QPushButton {
    padding: 12px 15px; /* Increase padding */
    font-size: 14px;
    text-align: left; /* Align text left */
    color: #495057; /* Medium gray text */
    background-color: transparent; /* Transparent background */
    border: none; /* No border */
    border-radius: 4px; /* Slightly rounded corners */
    margin-bottom: 5px; /* Space between buttons */
}

QPushButton:hover {
    background-color: #dee2e6; /* Lighter gray on hover */
    color: #212529; /* Darker text on hover */
}

QPushButton:checked { /* Style for the active/selected button */
    background-color: #007bff; /* Blue background */
    color: white; /* White text */
    font-weight: bold;
}

QPushButton:disabled { /* Style for disabled buttons */
    color: #adb5bd; /* Light gray text */
    background-color: transparent;
}

QPushButton#logout_button { /* Specific style for logout button */
    margin-top: 20px; /* Add space above logout */
    background-color: #dc3545; /* Red background */
    color: white;
    text-align: center; /* Center text */
}

QPushButton#logout_button:hover {
    background-color: #c82333; /* Darker red on hover */
}
"""


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
        self.nav_widget.setStyleSheet(NAV_STYLESHEET)  # Apply stylesheet

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

        # These buttons will be enabled after login
        nav_items = [
            ("challenges", "挑战列表", self.show_challenges),
            ("progress", "打卡记录", self.show_progress),
            ("reminders", "提醒设置", self.show_reminders),
            ("profile", "个人信息", self.show_profile),
        ]

        for item_id, label, callback in nav_items:
            button = QPushButton(label)
            button.setCheckable(True)  # Make buttons checkable
            button.clicked.connect(callback)
            button.clicked.connect(lambda checked, b=button: self.update_button_style(b))
            self.nav_buttons[item_id] = button
            self.nav_button_group.addButton(button)  # Add to group
            self.nav_layout.addWidget(button)
            button.setEnabled(False)  # Disabled until login

        # Add stretch to push logout button to bottom
        self.nav_layout.addStretch()

        # Logout button (initially hidden)
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")  # Set object name
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setVisible(False)
        self.nav_layout.addWidget(self.logout_button)

        # Add navigation to main layout
        self.main_layout.addWidget(self.nav_widget, 1)

    def setup_content_area(self):
        """Set up the content area with stacked widget."""
        self.content_widget = QStackedWidget()
        self.content_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #ffffff; /* White background for the container */
            }
            /* Default text, font, and background for widgets inside the content area */
            QWidget {
                font-family: "Helvetica Neue", Arial, sans-serif; /* Apply the font with fallbacks */
                font-size: 12pt; /* Apply the font size */
                color: #212529; /* Default dark text color */
                background-color: transparent; /* Default transparent background */
            }
            QLabel {
                background-color: transparent;
                color: #212529;
                /* Font is inherited from QWidget */
            }
            QGroupBox {
                background-color: transparent;
                border: 1px solid #ced4da; /* Add a light border to group boxes */
                border-radius: 4px;
                margin-top: 10px; /* Space above group box */
                padding-top: 15px; /* Space for the title */
                /* Font is inherited */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                margin-left: 10px; /* Indent title slightly */
                color: #495057; /* Medium gray title */
                font-weight: bold;
                background-color: #ffffff; /* Ensure title background matches main background */
                /* Font is inherited, but bold is added */
            }
            QFrame { /* Style for frames like ChallengeCard */
                background-color: #ffffff; /* White background for cards */
                border: 1px solid #dee2e6; /* Light border for cards */
                border-radius: 4px;
                /* Font is inherited */
            }
            QLineEdit, QTextEdit, QComboBox, QTimeEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                color: #212529;
                /* Font is inherited */
            }
            QTableWidget {
                background-color: #ffffff;
                color: #212529;
                gridline-color: #dee2e6;
                alternate-background-color: #f8f9fa;
                border: 1px solid #ced4da; /* Border around the table */
                /* Font is inherited */
            }
            QHeaderView::section {
                background-color: #e9ecef; /* Light gray header */
                color: #495057;
                padding: 5px;
                border: 1px solid #dee2e6;
                /* Font is inherited, consider making bold if needed */
                /* font-weight: bold; */
            }
            QCalendarWidget QWidget { /* Calendar background */
                alternate-background-color: #e9ecef; /* Background for month/year view */
            }
            QCalendarWidget QToolButton { /* Calendar navigation buttons */
                color: #007bff;
                /* Font is inherited */
            }
            /* General button style within content */
            QPushButton {
                padding: 8px 15px;
                /* font-size: 14px; */ /* Remove specific size to inherit */
                color: white;
                background-color: #007bff; /* Blue */
                border: none;
                border-radius: 4px;
                min-height: 30px;
                /* Font is inherited */
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #ced4da;
                color: #6c757d;
            }
            /* Specific button types */
            QPushButton#delete_button { /* Red delete/undo buttons */
                 background-color: #dc3545;
                 color: white;
            }
            QPushButton#delete_button:hover {
                 background-color: #c82333;
            }
            QPushButton#check_in_button { /* Green check-in button */
                background-color: #28a745;
                color: white;
            }
            QPushButton#check_in_button:hover {
                background-color: #218838;
            }
            QPushButton#subscribe_button { /* Blue subscribe button */
                background-color: #007bff;
                color: white;
            }
            QPushButton#subscribe_button:hover {
                background-color: #0056b3;
            }
            QPushButton#unsubscribe_button { /* Gray unsubscribe button */
                background-color: #6c757d;
                color: white;
            }
            QPushButton#unsubscribe_button:hover {
                background-color: #5a6268;
            }
            QCheckBox {
                spacing: 5px;
                color: #212529;
                /* Font is inherited */
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                color: #495057;
                /* Font is inherited */
            }
            QProgressBar::chunk {
                background-color: #007bff; /* Blue progress */
                border-radius: 4px;
            }
        """)

        # Create pages
        self.login_widget = LoginWidget(self.user_manager)
        self.register_widget = RegisterWidget(self.user_manager)
        self.challenge_widget = ChallengeListWidget(self.challenge_manager, self.progress_tracker)
        self.progress_widget = ProgressWidget(self.progress_tracker, self.challenge_manager)
        self.reminder_widget = ReminderWidget(self.reminder_scheduler, self.challenge_manager)
        self.profile_widget = ProfileWidget(self.user_manager, self.progress_tracker)

        # Add pages to stacked widget
        self.content_widget.addWidget(self.login_widget)
        self.content_widget.addWidget(self.register_widget)
        self.content_widget.addWidget(self.challenge_widget)
        self.content_widget.addWidget(self.progress_widget)
        self.content_widget.addWidget(self.reminder_widget)
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
        self.user_changed.connect(self.progress_widget.set_user)
        self.user_changed.connect(self.reminder_widget.set_user)
        self.user_changed.connect(self.profile_widget.set_user)

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
        if "challenges" in self.nav_buttons:
            button = self.nav_buttons["challenges"]
            if not button.isChecked():
                button.setChecked(True)
            self.update_button_style(button)

    def show_progress(self):
        """Show the progress page."""
        self.content_widget.setCurrentWidget(self.progress_widget)
        if "progress" in self.nav_buttons:
            button = self.nav_buttons["progress"]
            if not button.isChecked():
                button.setChecked(True)
            self.update_button_style(button)

    def show_reminders(self):
        """Show the reminders page."""
        self.content_widget.setCurrentWidget(self.reminder_widget)
        if "reminders" in self.nav_buttons:
            button = self.nav_buttons["reminders"]
            if not button.isChecked():
                button.setChecked(True)
            self.update_button_style(button)

    def show_profile(self):
        """Show the profile page."""
        self.content_widget.setCurrentWidget(self.profile_widget)
        if "profile" in self.nav_buttons:
            button = self.nav_buttons["profile"]
            if not button.isChecked():
                button.setChecked(True)
            self.update_button_style(button)

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
        for button in self.nav_buttons.values():
            button.style().unpolish(button)
            button.style().polish(button)
