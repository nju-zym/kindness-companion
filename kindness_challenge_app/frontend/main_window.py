from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QFont

from .user_auth import LoginWidget, RegisterWidget
from .challenge_ui import ChallengeListWidget
from .progress_ui import ProgressWidget
from .reminder_ui import ReminderWidget
from .profile_ui import ProfileWidget


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
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setAlignment(Qt.AlignTop)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)
        self.nav_layout.setSpacing(10)
        
        # App title
        self.title_label = QLabel("善行挑战")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.nav_layout.addWidget(self.title_label)
        
        # Add some spacing
        self.nav_layout.addSpacing(20)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        # These buttons will be enabled after login
        nav_items = [
            ("challenges", "挑战列表", self.show_challenges),
            ("progress", "打卡记录", self.show_progress),
            ("reminders", "提醒设置", self.show_reminders),
            ("profile", "个人信息", self.show_profile),
        ]
        
        for item_id, label, callback in nav_items:
            button = QPushButton(label)
            button.setMinimumHeight(40)
            button.clicked.connect(callback)
            self.nav_buttons[item_id] = button
            self.nav_layout.addWidget(button)
            button.setEnabled(False)  # Disabled until login
        
        # Add stretch to push logout button to bottom
        self.nav_layout.addStretch()
        
        # Logout button (initially hidden)
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setMinimumHeight(40)
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
        
        # Show logout button
        self.logout_button.setVisible(True)
        
        # Emit user_changed signal
        self.user_changed.emit(user)
        
        # Show challenges page
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
        
        # Hide logout button
        self.logout_button.setVisible(False)
        
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
    
    def show_progress(self):
        """Show the progress page."""
        self.content_widget.setCurrentWidget(self.progress_widget)
    
    def show_reminders(self):
        """Show the reminders page."""
        self.content_widget.setCurrentWidget(self.reminder_widget)
    
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
