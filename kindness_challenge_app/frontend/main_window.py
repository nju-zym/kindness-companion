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
QWidget#nav_widget {
    background-color: palette(window); /* Use window background color */
    border-right: 1px solid palette(mid); /* Use mid border */
    min-width: 180px;
    max-width: 220px;
}

QLabel#title_label {
    font-size: 18pt;
    font-weight: bold; /* Make title bolder */
    color: palette(highlight); /* Use highlight color for title */
    padding: 20px 10px;
    margin-bottom: 10px;
    font-family: "Helvetica Neue", Arial, sans-serif;
    border-bottom: 1px solid palette(mid); /* Use mid border */
}

QPushButton {
    padding: 10px 15px;
    font-size: 11pt;
    text-align: left;
    color: palette(text); /* Use text color for better contrast */
    background-color: transparent;
    border: none;
    border-radius: 5px;
    margin: 2px 10px;
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-weight: 500; /* Slightly bolder */
}

QPushButton:hover {
    background-color: palette(highlight); /* Use highlight color on hover */
    color: palette(highlightedText); /* Use highlighted text color on hover */
}

QPushButton:checked {
    background-color: palette(highlight); /* Use highlight color for checked */
    color: palette(highlightedText); /* Use highlighted text color for checked */
    font-weight: bold; /* Make checked button bold */
}

QPushButton:disabled {
    color: palette(disabled, buttonText); /* Use disabled button text color */
    background-color: transparent;
}

QPushButton#logout_button {
    margin: 20px 10px 10px 10px;
    background-color: palette(mid); /* Use mid-tone background */
    color: palette(windowText); /* Use window text for better contrast */
    text-align: center;
    font-weight: 500;
}

QPushButton#logout_button:hover {
    background-color: palette(dark); /* Use dark color on hover */
    color: palette(brightText); /* Ensure text is readable */
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
        # Apply a more comprehensive and modern stylesheet using palette colors
        self.content_widget.setStyleSheet("""
            /* Base styling for the content area container */
            QStackedWidget {
                background-color: palette(window); /* Use window background */
                padding: 15px; /* Reduced padding */
            }

            /* Default font and color for all widgets within the content area */
            QWidget {
                font-family: "Helvetica Neue", Arial, sans-serif;
                font-size: 11pt;
                color: palette(windowText); /* Use window text color */
                background-color: transparent;
            }

            /* Labels */
            QLabel {
                background-color: transparent;
                padding: 2px;
                margin-bottom: 5px; /* Consistent margin */
            }
            QLabel#error_label {
                color: palette(negative); /* Use palette color for errors */
                font-size: 9pt;
            }
            QLabel#title_label {
                font-size: 18pt; /* Slightly larger title */
                font-weight: bold; /* Make title bolder */
                color: palette(highlight); /* Use highlight color for titles */
                margin-bottom: 15px; /* Reduced space below title */
                border-bottom: 1px solid palette(mid); /* Use mid border */
                padding-bottom: 5px; /* Reduced padding below title */
            }
            QLabel#streak_label {
                color: palette(positive); /* Use positive palette color for streak */
                font-weight: bold; /* Make streak bold */
            }

            /* Group Boxes */
            QGroupBox {
                background-color: palette(base); /* Use base background for group boxes */
                border: 1px solid palette(mid); /* Use mid border */
                border-radius: 6px; /* Slightly more rounded */
                margin-top: 10px; /* Reduced margin */
                padding: 20px 15px 15px 15px; /* Reduced padding */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 12px; /* Adjust padding */
                margin-left: 15px; /* Adjust margin */
                color: palette(windowText);
                font-weight: bold; /* Make group box title bold */
                background-color: palette(window); /* Match window background */
                border: 1px solid palette(mid); /* Use mid border */
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            /* Frames (e.g., ChallengeCard) */
            QFrame#challenge_card {
                background-color: palette(base);
                border: 1px solid palette(mid); /* Use mid border */
                border-radius: 6px;
                padding: 15px; /* Reduced padding */
                margin-bottom: 10px; /* Reduced margin */
            }
            QFrame#challenge_card:hover {
                 border-color: palette(highlight);
            }
            /* Style for title inside challenge card */
            QFrame#challenge_card QLabel#title_label {
                 font-size: 14pt; /* Adjust size for card */
                 font-weight: bold;
                 color: palette(text); /* Use standard text color */
                 margin-bottom: 8px;
                 border-bottom: none; /* No border inside card */
                 padding-bottom: 0;
            }


            /* Input Fields */
            QLineEdit, QTextEdit, QComboBox, QTimeEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
                background-color: palette(base); /* Use base background */
                border: 1px solid palette(mid);
                border-radius: 5px; /* Consistent radius */
                padding: 9px 12px; /* Adjust padding */
                color: palette(text);
                min-height: 28px; /* Adjust height */
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QTimeEdit:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: palette(highlight);
                outline: 0;
            }
            QComboBox::drop-down {
                border-left: 1px solid palette(mid);
                padding-right: 8px; /* Adjust padding */
            }
            QComboBox::down-arrow {
                 /* Consider using a theme-aware icon or SVG */
                 /* image: url(path/to/your/arrow.svg); */
                 width: 14px;
                 height: 14px;
            }

            /* Tables */
            QTableWidget {
                background-color: palette(base);
                color: palette(text);
                gridline-color: palette(midlight); /* Keep grid lines light */
                alternate-background-color: palette(alternate-base);
                border: 1px solid palette(dark); /* Use dark border for outline */
                border-radius: 5px;
                selection-background-color: palette(highlight);
                selection-color: palette(highlightedText);
            }
            QHeaderView::section {
                background-color: palette(light);
                color: palette(text);
                padding: 10px 5px; /* Adjust padding */
                border: none;
                border-bottom: 1px solid palette(dark); /* Use dark border */
                font-weight: bold; /* Make header bold */
            }
            QHeaderView::section:horizontal {
                border-right: 1px solid palette(mid); /* Use mid border for vertical lines */
            }
            QHeaderView::section:vertical {
                 border-bottom: 1px solid palette(mid); /* Use mid border for horizontal lines */
            }
            QTableCornerButton::section {
                 background-color: palette(light);
                 border: none;
                 border-bottom: 1px solid palette(dark); /* Use dark border */
                 border-right: 1px solid palette(dark); /* Use dark border */
            }

            /* Calendar Widget */
            QCalendarWidget QWidget {
                alternate-background-color: palette(alternate-base);
            }
            QCalendarWidget QToolButton {
                color: palette(buttonText);
                background-color: transparent;
                border: none;
                padding: 6px; /* Adjust padding */
                margin: 2px;
                border-radius: 4px; /* Consistent radius */
            }
             QCalendarWidget QToolButton:hover {
                 background-color: palette(highlight);
                 color: palette(highlightedText);
             }
            #qt_calendar_navigationbar {
                 background-color: palette(light);
                 border-bottom: 1px solid palette(dark); /* Use dark border */
            }
            #qt_calendar_prevmonth, #qt_calendar_nextmonth {
                 qproperty-iconSize: 18px 18px; /* Adjust icon size */
                 padding: 6px; /* Adjust padding */
            }
            #qt_calendar_monthbutton, #qt_calendar_yearbutton {
                 font-weight: bold; /* Make month/year bold */
                 padding: 6px 12px; /* Adjust padding */
            }
            #qt_calendar_calendarview {
                 background-color: palette(base);
                 alternate-background-color: palette(alternate-base);
                 selection-background-color: palette(highlight);
                 selection-color: palette(highlightedText);
            }
            /* Highlight today's date */
            #qt_calendar_calendarview::item:selected:!disabled {
                 background-color: palette(highlight);
                 color: palette(highlightedText);
            }
            /* Highlight dates with check-ins (using background role) */
            #qt_calendar_calendarview::item[dateTextFormat="true"] {
                 background-color: palette(positive);
                 color: palette(brightText);
                 border-radius: 3px;
            }


            /* General Button Style within Content Area */
            QPushButton {
                padding: 9px 20px; /* Adjust padding */
                font-size: 10pt;
                color: palette(buttonText);
                background-color: palette(button);
                border: none;
                border-radius: 5px; /* Consistent radius */
                min-height: 34px; /* Adjust height */
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: palette(dark);
            }
            QPushButton:pressed {
                background-color: palette(shadow);
            }
            QPushButton:disabled {
                background-color: palette(disabled, button);
                color: palette(disabled, buttonText);
            }

            /* Specific Button Types (using object names) - Use palette colors */
            QPushButton#delete_button, QPushButton#undo_button {
                 background-color: palette(negative); /* Use negative palette color */
                 color: palette(brightText); /* Ensure contrast */
            }
            QPushButton#delete_button:hover, QPushButton#undo_button:hover {
                 /* Define hover state if needed, maybe darken the negative color */
                 background-color: #dc3545; /* Slightly darker red */
            }
            QPushButton#delete_button:pressed, QPushButton#undo_button:pressed {
                 /* Define pressed state if needed, maybe use shadow */
                 background-color: #bd2130; /* Even darker red */
            }

            QPushButton#check_in_button, QPushButton#save_button, QPushButton#add_button, QPushButton#create_button {
                background-color: palette(positive); /* Use positive palette color */
                color: palette(brightText); /* Ensure contrast */
            }
            QPushButton#check_in_button:hover, QPushButton#save_button:hover, QPushButton#add_button:hover, QPushButton#create_button:hover {
                background-color: #218838; /* Slightly darker green */
            }
             QPushButton#check_in_button:pressed, QPushButton#save_button:pressed, QPushButton#add_button:pressed, QPushButton#create_button:pressed {
                background-color: #1e7e34; /* Even darker green */
            }

            QPushButton#subscribe_button {
                background-color: palette(highlight); /* Use highlight for subscribe */
                color: palette(highlightedText);
            }
            QPushButton#subscribe_button:hover {
                background-color: palette(dark);
            }
             QPushButton#subscribe_button:pressed {
                background-color: palette(shadow);
            }

            QPushButton#unsubscribe_button, QPushButton#cancel_button {
                background-color: palette(mid); /* Use mid-tone for secondary actions */
                color: palette(windowText);
            }
            QPushButton#unsubscribe_button:hover, QPushButton#cancel_button:hover {
                background-color: palette(dark);
                color: palette(brightText); /* Ensure text readable on dark hover */
            }
             QPushButton#unsubscribe_button:pressed, QPushButton#cancel_button:pressed {
                background-color: palette(shadow);
            }

            /* CheckBox */
            QCheckBox {
                spacing: 10px; /* Increase spacing */
                color: palette(text);
            }
            QCheckBox::indicator {
                width: 18px; /* Slightly larger */
                height: 18px;
                border: 1px solid palette(dark); /* Use dark border */
                border-radius: 4px; /* Consistent radius */
                background-color: palette(base);
            }
            QCheckBox::indicator:checked {
                background-color: palette(highlight);
                border-color: palette(highlight);
                 /* Consider using a theme-aware icon or SVG */
                 /* image: url(path/to/your/checkmark.svg); */
            }
            QCheckBox::indicator:hover {
                border-color: palette(dark);
            }

            /* Progress Bar */
            QProgressBar {
                border: 1px solid palette(dark); /* Use dark border */
                border-radius: 6px; /* Consistent radius */
                text-align: center;
                color: palette(text);
                background-color: palette(light);
                min-height: 22px; /* Adjust height */
            }
            QProgressBar::chunk {
                background-color: palette(positive); /* Use positive palette color */
                border-radius: 5px; /* Consistent radius */
                margin: 1px;
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
