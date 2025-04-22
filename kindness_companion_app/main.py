import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import QFile, QTextStream  # Added for QSS loading
import logging  # Added for logger access

from frontend.main_window import MainWindow
from backend.database_manager import DatabaseManager
from backend.user_manager import UserManager
from backend.challenge_manager import ChallengeManager
from backend.progress_tracker import ProgressTracker
from backend.reminder_scheduler import ReminderScheduler
from backend.utils import setup_logging


def main():
    """Main application entry point."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Kindness Challenge application")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("善行挑战")

    # Set application icon
    icon_path = "kindness_challenge_app/resources/icons/app_icon.png" # Assuming the icon is named app_icon.png
    app_icon = QIcon(icon_path)
    if app_icon.isNull():
        logger.warning(f"Could not load application icon from {icon_path}. Using default icon.")
    else:
        app.setWindowIcon(app_icon)
        logger.info(f"Loaded application icon from {icon_path}")

    # Set application font
    font = QFont("Helvetica Neue", 18)  # Use Helvetica Neue, size 18
    app.setFont(font)

    # --- Theme Selection --- #
    # Set this variable to 'light' or 'dark' to choose the theme
    CURRENT_THEME = "dark" # Or "light"
    # ----------------------- #

    # Load and apply stylesheet based on theme
    style_file_name = "main.qss" if CURRENT_THEME == "light" else "dark.qss"
    style_file_path = f"kindness_challenge_app/resources/styles/{style_file_name}"
    style_file = QFile(style_file_path)
    if style_file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(style_file)
        app.setStyleSheet(stream.readAll())
        style_file.close()
        logger.info(f"Loaded {CURRENT_THEME} theme stylesheet from {style_file_path}")
    else:
        logger.warning(f"Could not load stylesheet from {style_file_path}. Error: {style_file.errorString()}")

    # Initialize backend components
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    challenge_manager = ChallengeManager(db_manager)
    progress_tracker = ProgressTracker(db_manager)

    # Add default user if it doesn't exist
    default_user = user_manager.login("zym", "1")
    if not default_user:
        logger.info("Creating default user 'zym'")
        user_manager.register_user("zym", "1")

    # Create and show main window
    main_window = MainWindow(
        user_manager,
        challenge_manager,
        progress_tracker,
        ReminderScheduler(db_manager)
    )
    main_window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
