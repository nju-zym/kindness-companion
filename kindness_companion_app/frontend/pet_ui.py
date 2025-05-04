import logging
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QLineEdit, QPushButton, QSizePolicy
)
from PySide6.QtCore import Slot, Qt, QTimer, QSize
from PySide6.QtGui import QMovie, QPainter, QBitmap, QPainterPath, QRegion, QIcon

# Enhanced logging for debugging import issues
logger = logging.getLogger(__name__)
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"sys.path: {sys.path}")

# Try to import the AI handler function with better error handling
try:
    # First try relative import
    from ai_core.pet_handler import handle_pet_event
    logger.info("Successfully imported handle_pet_event using relative import")
except ImportError as e:
    logger.error(f"Failed to import handle_pet_event using relative import: {e}")

    # Try absolute import
    try:
        from kindness_companion_app.ai_core.pet_handler import handle_pet_event
        logger.info("Successfully imported handle_pet_event using absolute import")
    except ImportError as e:
        logger.error(f"Failed to import handle_pet_event using absolute import: {e}")

        # Try to add parent directory to sys.path and retry
        try:
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                logger.info(f"Added {parent_dir} to sys.path")

            from ai_core.pet_handler import handle_pet_event
            logger.info("Successfully imported handle_pet_event after path adjustment")
        except ImportError as e:
            logger.error(f"All import attempts failed: {e}")
            logger.error("AI pet features will be disabled.")
            handle_pet_event = None  # type: ignore

# Import UserManager
from backend.user_manager import UserManager

logger = logging.getLogger(__name__)

class PetWidget(QWidget):
    def __init__(self, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = None
        self._pending_event = None
        self.movie = None  # Initialize movie attribute
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center content

        # Label to display the Pet Animation (GIF)
        self.pet_animation_label = QLabel()
        self.pet_animation_label.setObjectName("pet_animation_label")  # Add object name for styling
        self.pet_animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_animation_label.setMinimumSize(QSize(200, 200))
        layout.addWidget(self.pet_animation_label)

        # Dialogue Bubble
        self.dialogue_label = QLabel("")
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setStyleSheet("""
            background-color: #e0f7fa;
            border: 1px solid #b2ebf2;
            border-radius: 10px;
            padding: 10px;
            margin-top: 10px;
            font-size: 14px;
        """)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setVisible(False)  # Initially hidden
        layout.addWidget(self.dialogue_label)

        # Status Label
        self.pet_status_label = QLabel("你好！今天感觉怎么样？")
        self.pet_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_status_label.setStyleSheet("font-style: italic; color: gray; margin-top: 5px;")
        layout.addWidget(self.pet_status_label)

        # Chat Input Area
        chat_layout = QHBoxLayout()
        chat_layout.setContentsMargins(10, 10, 10, 10)

        # Message input field
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("和宠物聊天...")
        self.message_input.setMinimumHeight(36)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #b2ebf2;
                border-radius: 18px;
                padding: 5px 15px;
                background-color: #f5f5f5;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4dd0e1;
                background-color: white;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)

        # Send button
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(":/icons/send.png"))  # Assuming you have a send icon in resources
        self.send_button.setFixedSize(36, 36)
        self.send_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 18px;
                background-color: #4dd0e1;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #26c6da;
            }
            QPushButton:pressed {
                background-color: #00bcd4;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        # Add widgets to chat layout
        chat_layout.addWidget(self.message_input, 1)  # Stretch factor 1
        chat_layout.addWidget(self.send_button, 0)    # No stretch

        # Add chat layout to main layout
        layout.addLayout(chat_layout)

        # Timer to hide dialogue after a while
        self.dialogue_timer = QTimer(self)
        self.dialogue_timer.setSingleShot(True)
        self.dialogue_timer.timeout.connect(lambda: self.dialogue_label.setVisible(False))

    def resizeEvent(self, event):
        """Apply a circular mask whenever the widget is resized."""
        super().resizeEvent(event)
        rect = self.pet_animation_label.rect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            mask_region = QRegion(rect, QRegion.Ellipse)
            self.pet_animation_label.setMask(mask_region)
        else:
            self.pet_animation_label.clearMask()

    @Slot(str, dict)
    def send_event_to_pet(self, event_type: str, event_data: dict):
        """Receives events from other parts of the app and triggers AI processing."""
        if not self.current_user:
            logger.warning("Cannot send event to pet: No user logged in.")
            return

        user_id = self.current_user.get('id')
        if not user_id:
            logger.error("Cannot send event to pet: User ID is missing.")
            return

        # --- AI Consent Check Removed ---
        # AI consent is now assumed True by default.
        logger.info(f"AI consent assumed True for user {user_id}. Proceeding with event: {event_type}")
        self._call_ai_handler(user_id, event_type, event_data)
        # --- End AI Consent Check Removed ---

    def _call_ai_handler(self, user_id: int, event_type: str, event_data: dict):
        """Internal method to actually call the AI handler."""
        logger.info(f"Calling AI core: User {user_id}, Type: {event_type}, Data: {event_data}")
        self.pet_status_label.setText("正在思考...")  # Changed thinking text

        # Check if handle_pet_event is available
        if handle_pet_event is None:
            logger.error("Cannot call AI handler: handle_pet_event is None")
            self.update_pet_display({"dialogue": "AI 功能未正确加载。请检查日志。", "suggested_animation": "confused"})
            return

        try:
            # Log the type of handle_pet_event for debugging
            logger.info(f"handle_pet_event type: {type(handle_pet_event)}")
            logger.info(f"handle_pet_event callable: {callable(handle_pet_event)}")

            # Call the AI handler
            logger.info("About to call handle_pet_event...")
            response = handle_pet_event(user_id, event_type, event_data)
            logger.info(f"Received AI response: {response}")
            self.update_pet_display(response)
        except Exception as e:
            logger.error(f"Error calling handle_pet_event: {e}", exc_info=True)
            self.update_pet_display({"dialogue": "哎呀！好像出错了。", "suggested_animation": "confused"})  # Example error state

    def update_pet_display(self, response: dict):
        """Updates the pet animation GIF and dialogue bubble."""
        dialogue = response.get('dialogue', "")
        suggested_animation = response.get('suggested_animation', "idle")
        logger.info(f"Updating pet display. Animation: {suggested_animation}, Dialogue: '{dialogue[:20]}...'")

        # Update dialogue bubble
        self.dialogue_label.setText(dialogue)
        self.dialogue_label.setVisible(bool(dialogue))
        if dialogue:
            self.dialogue_timer.start(8000)  # Hide dialogue after 8 seconds

        # --- Update Status Label Text based on animation ---
        status_text_map = {
            "idle": "正在休息...",
            "happy": "看起来很开心！",
            "excited": "好兴奋呀！",
            "concerned": "有点担心...",
            "confused": "嗯？怎么了？",
            # Add other mappings as needed
        }
        self.pet_status_label.setText(status_text_map.get(suggested_animation, "正在休息..."))

        # --- Update Animation GIF ---
        gif_path = f":/animations/{suggested_animation}.gif"
        logger.debug(f"Attempting to load animation from: {gif_path}")

        # Stop the current movie if it's running
        if self.movie and self.movie.state() == QMovie.Running:
            logger.debug("Stopping previous movie.")
            self.movie.stop()

        # Create and set the new movie
        self.movie = QMovie(gif_path)
        is_valid = self.movie.isValid()
        logger.debug(f"Movie created. Is valid: {is_valid}")

        if is_valid:
            self.pet_animation_label.setMovie(self.movie)
            logger.debug("Movie set on label.")

            # --- Ensure label has size before scaling and applying mask --- START
            def apply_scaling_and_mask():
                label_size = self.pet_animation_label.size()
                size_valid = label_size.isValid() and label_size.width() > 0 and label_size.height() > 0
                logger.debug(f"apply_scaling_and_mask called. Label size: {label_size.width()}x{label_size.height()}, Is valid: {size_valid}")

                if size_valid:
                    logger.debug(f"Label size valid. Scaling movie to {label_size.width()}x{label_size.height()} and applying mask.")
                    self.movie.setScaledSize(label_size)
                    self.resizeEvent(None) # Force mask update using current size
                    logger.debug("Starting movie...")
                    self.movie.start()
                    logger.debug(f"Movie state after start(): {self.movie.state()}") # Log state after starting
                else:
                    # If size is still not valid, try again slightly later
                    logger.warning("Label size not valid yet. Retrying mask/scale shortly.")
                    QTimer.singleShot(50, apply_scaling_and_mask)

            # Start the process, potentially deferred if size isn't ready
            logger.debug("Initiating apply_scaling_and_mask.")
            apply_scaling_and_mask()
            # --- Ensure label has size before scaling and applying mask --- END

        else:
            logger.warning(f"Failed to load animation: {gif_path}. Displaying fallback text.")
            self.pet_animation_label.setMovie(None) # Clear any previous movie
            self.pet_animation_label.setText("🐾") # Set fallback text
            self.pet_animation_label.clearMask() # Clear mask if animation failed

    def send_message(self):
        """Handles sending a user message to the pet."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "无法发送", "请先登录。")
            return

        user_message = self.message_input.text().strip()
        if not user_message:
            return

        user_id = self.current_user.get('id')

        # --- AI Consent Check Removed ---
        logger.info(f"AI consent assumed True for user {user_id}. Proceeding with sending message.")
        # --- End AI Consent Check Removed ---

        # Clear input and show thinking state
        self.message_input.clear()
        self.pet_status_label.setText("正在思考...")

        # Prepare event data
        event_data = {"message": user_message}

        # Call the AI handler
        self._call_ai_handler(user_id, "user_message", event_data)

    @Slot(dict)
    def set_user(self, user: dict | None):
        """Sets the current user and initializes/clears pet state."""
        self.current_user = user
        if user:
            user_id = user.get('id')
            logger.info(f"PetWidget set user: {user_id}")

            # --- AI Consent Check Removed ---
            # Always show pet container if user is logged in
            self.pet_container.setVisible(True)
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.pet_status_label.setText("你好！今天感觉怎么样？")
            # Load initial pet state or default animation
            self.update_pet_display({"dialogue": "你好！很高兴见到你！", "suggested_animation": "idle"})
            logger.info(f"AI consent assumed True for user {user_id}. Pet UI enabled.")
            # --- End AI Consent Check Removed ---

        else:
            logger.info("PetWidget user set to None (logged out).")
            # Clear pet state and hide UI elements
            self.pet_animation_label.clear()
            self.dialogue_label.setText("")
            self.dialogue_label.setVisible(False)
            self.pet_status_label.setText("请先登录")
            self.message_input.clear()
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.pet_container.setVisible(False) # Hide the container when logged out
