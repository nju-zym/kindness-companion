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

# Import UserManager and AIConsentDialog
from backend.user_manager import UserManager
from .widgets.ai_consent_dialog import AIConsentDialog

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
        """Receives events from other parts of the app and triggers AI processing, checking consent first."""
        if not self.current_user:
            logger.warning("Cannot handle pet event: No user logged in.")
            return
        if not handle_pet_event:
            logger.error("handle_pet_event is not available. Cannot process pet event.")
            self.update_pet_display({"dialogue": "(AI Core not loaded)", "suggested_animation": "idle"})
            return

        user_id = self.current_user.get('id')
        if not user_id:
            logger.error("Cannot handle pet event: User ID not found.")
            return

        # --- Check AI Consent ---
        consent_status = self.user_manager.get_ai_consent(user_id)
        logger.info(f"AI consent status for user {user_id}: {consent_status}")

        if consent_status is True:
            # Consent granted, proceed with AI call
            logger.info(f"AI consent granted for user {user_id}. Proceeding with event.")
            self._call_ai_handler(user_id, event_type, event_data)
        elif consent_status is False:
            # Consent explicitly denied
            logger.info(f"AI features disabled for user {user_id} due to denied consent.")
            self.update_pet_display({"dialogue": "AI 功能已禁用。\n您可以在设置中更改。", "suggested_animation": "idle"})
        else:  # consent_status is None (not set yet)
            logger.info(f"AI consent not set for user {user_id}. Showing consent dialog.")
            # Store the event that triggered this check
            self._pending_event = (event_type, event_data)
            # Show the consent dialog
            self._show_consent_dialog(user_id)

    def _show_consent_dialog(self, user_id: int):
        """Shows the AI consent dialog to the user."""
        dialog = AIConsentDialog(self)
        # Connect the signal from the dialog to a handler method
        dialog.consent_changed.connect(lambda consented: self._handle_consent_result(user_id, consented))
        dialog.exec()  # Show the dialog modally

    @Slot(int, bool)
    def _handle_consent_result(self, user_id: int, consented: bool):
        """Handles the result from the AIConsentDialog."""
        logger.info(f"User {user_id} responded to AI consent dialog: {consented}")
        # Save the consent status to the database
        success = self.user_manager.set_ai_consent(user_id, consented)
        logger.info(f"AI consent update successful: {success}")

        if consented and success:
            # Consent granted, process the pending event if any
            if self._pending_event:
                event_type, event_data = self._pending_event
                self._pending_event = None  # Clear pending event
                logger.info(f"Processing pending event after consent: {event_type}")
                # Use QTimer.singleShot to ensure the dialog is fully closed before proceeding
                QTimer.singleShot(0, lambda: self._call_ai_handler(user_id, event_type, event_data))
            else:
                logger.info("Consent granted, but no pending event.")
                self.update_pet_display({"dialogue": "AI 功能已启用！", "suggested_animation": "idle_happy"})
        elif not consented:
            # Consent denied, update display accordingly
            logger.info("Consent denied by user.")
            self.update_pet_display({"dialogue": "AI 功能未启用。", "suggested_animation": "idle"})
            self._pending_event = None  # Clear pending event if consent denied
        elif consented and not success:
            logger.error(f"Failed to update AI consent status for user {user_id} in the database.")
            self.update_pet_display({"dialogue": "保存同意状态时出错。", "suggested_animation": "confused"})
            self._pending_event = None

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
        message = self.message_input.text().strip()
        if not message:
            return  # Don't send empty messages

        logger.info(f"User sent message to pet: {message}")

        # Clear the input field
        self.message_input.clear()

        # Create event data with the user's message
        event_data = {'message': message}

        # Send the event to the pet
        self.send_event_to_pet('user_message', event_data)

    @Slot(dict)
    def set_user(self, user: dict | None):
        """Sets the current user and initializes/clears pet state."""
        self.current_user = user
        self._pending_event = None  # Clear any pending event on user change
        if user:
            logger.info(f"Pet UI activated for user: {user.get('id')}")
            self.update_pet_display({"dialogue": "", "suggested_animation": "idle"})
            self.pet_status_label.setText("准备好迎接新的善举了吗？")  # Changed logged-in text
            QTimer.singleShot(0, lambda: self.resizeEvent(None))  # Force mask update

            # Enable chat input when user is logged in
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            logger.info("Pet UI deactivated (user logged out).")
            self.update_pet_display({"dialogue": "", "suggested_animation": "idle"})
            self.dialogue_label.setVisible(False)
            self.pet_status_label.setText("再见！")  # Changed logged-out text
            QTimer.singleShot(0, lambda: self.resizeEvent(None))  # Force mask update

            # Disable chat input when no user is logged in
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
