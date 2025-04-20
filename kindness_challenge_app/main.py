import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

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
    
    # Initialize backend components
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    challenge_manager = ChallengeManager(db_manager)
    progress_tracker = ProgressTracker(db_manager)
    
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
