import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon

# Assuming AnimatedMessageBox is in a reachable path, e.g., frontend.widgets
try:
    # Corrected relative import
    from .animated_message_box import AnimatedMessageBox
except ImportError:
    # Fallback if running the file directly or structure is different
    # This fallback might still be problematic depending on execution context
    from animated_message_box import AnimatedMessageBox


class AISettingsWidget(QWidget):
    """
    Widget for managing AI feature settings and consent.
    """

    ai_consent_changed = Signal(bool)  # Emits the new consent status

    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = None
        self._is_toggling_consent = False  # Flag to prevent re-entry

        self.setup_ui()

    def setup_ui(self):
        """Set up the AI settings UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # No margins for the main widget layout
        main_layout.setSpacing(12)

        # --- AI Settings Section with improved styling ---
        ai_frame = QFrame()
        ai_frame.setObjectName("ai_frame")
        ai_frame.setStyleSheet(
            """
            QFrame#ai_frame {
                background-color: rgba(40, 40, 40, 0.5);
                border-radius: 8px;
                padding: 10px;
            }
        """
        )

        ai_settings_layout = QVBoxLayout(ai_frame)
        ai_settings_layout.setContentsMargins(15, 15, 15, 15)
        ai_settings_layout.setSpacing(12)

        # AI settings title
        ai_title = QLabel("AI 功能设置")
        ai_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #4FC3F7;")
        ai_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_settings_layout.addWidget(ai_title)

        # AI consent checkbox with improved styling
        self.ai_consent_checkbox = QCheckBox("启用 AI 功能")
        self.ai_consent_checkbox.setObjectName("ai_checkbox")
        self.ai_consent_checkbox.setToolTip("启用或禁用 AI 电子宠物和智能报告功能")
        self.ai_consent_checkbox.stateChanged.connect(self.toggle_ai_consent)
        self.ai_consent_checkbox.setStyleSheet(
            """
            QCheckBox#ai_checkbox {
                font-weight: bold;
                color: #4FC3F7;
                font-size: 16px;
            }
            QCheckBox#ai_checkbox::indicator {
                width: 22px;
                height: 22px;
            }
        """
        )

        # AI features explanation with improved styling
        ai_info_frame = QFrame()
        ai_info_frame.setObjectName("ai_info_frame")
        ai_info_frame.setStyleSheet(
            """
            QFrame#ai_info_frame {
                background-color: rgba(30, 30, 30, 0.7);
                border-radius: 5px;
                padding: 5px;
            }
        """
        )

        ai_info_layout = QVBoxLayout(ai_info_frame)
        ai_info_layout.setContentsMargins(10, 10, 10, 10)

        ai_info_label = QLabel(
            "启用后，应用将使用 AI 功能增强您的体验：\\n"
            "• AI 电子宠物互动\\n"
            "• 个性化善举报告\\n\\n"
            "这需要将部分数据发送至第三方 AI 服务。"
        )
        ai_info_label.setWordWrap(True)
        ai_info_label.setStyleSheet("color: #ddd; font-size: 14px; line-height: 150%;")
        ai_info_layout.addWidget(ai_info_label)

        # Add widgets to layout
        ai_settings_layout.addWidget(self.ai_consent_checkbox)
        ai_settings_layout.addWidget(ai_info_frame)

        main_layout.addWidget(ai_frame)

    @Slot(dict)
    def set_user(self, user):
        """Sets the current user and updates the checkbox state."""
        # ADD CHECK HERE: If a toggle is in progress, skip this update to prevent conflicts
        if self._is_toggling_consent:
            logging.getLogger(__name__).debug(
                "AISettingsWidget.set_user skipped during toggle operation."
            )
            return

        logger = logging.getLogger(__name__)
        self.current_user = user
        if user:
            ai_consent = user.get(
                "ai_consent_given", False
            )  # Default to False if missing
            logger.info(
                f"AISettingsWidget: Setting AI consent checkbox based on user data: {ai_consent}"
            )
            self.ai_consent_checkbox.blockSignals(True)
            self.ai_consent_checkbox.setChecked(bool(ai_consent))  # Ensure boolean
            self.ai_consent_checkbox.blockSignals(False)
            self.ai_consent_checkbox.setEnabled(True)
        else:
            logger.info(
                "AISettingsWidget: User is None. Disabling and unchecking AI consent checkbox."
            )
            self.ai_consent_checkbox.blockSignals(True)
            self.ai_consent_checkbox.setChecked(False)
            self.ai_consent_checkbox.setEnabled(
                False
            )  # Disable checkbox when logged out
            self.ai_consent_checkbox.blockSignals(False)

    @Slot(int)
    def toggle_ai_consent(self, state):
        """
        Toggle AI consent status when the checkbox is clicked.

        Args:
            state (int): Qt.Checked (2) if checked, Qt.Unchecked (0) if unchecked
        """
        logging.getLogger(__name__).info(
            f"toggle_ai_consent received state: {state} (Qt.CheckState.Checked={Qt.CheckState.Checked}, Qt.CheckState.Unchecked={Qt.CheckState.Unchecked})"
        )

        if self._is_toggling_consent:
            return
        self._is_toggling_consent = True

        try:
            logger = logging.getLogger(__name__)
            logger.debug(
                f"AISettingsWidget.toggle_ai_consent called with state: {state}"
            )

            if not self.current_user:
                logger.warning("Cannot toggle AI consent: No user logged in")
                return

            user_id = self.current_user.get("id")
            if not user_id:
                logger.error("Cannot toggle AI consent: User ID not found")
                return

            consent_status = state == Qt.CheckState.Checked
            logger.info(f"Setting AI consent for user {user_id} to: {consent_status}")

            success = self.user_manager.set_ai_consent(user_id, consent_status)
            logger.info(f"user_manager.set_ai_consent returned: {success}")

            if success:
                logger.debug(
                    "Reset _is_toggling_consent flag before showing message/emitting signal."
                )

                # Show confirmation message *directly* based on consent_status
                if consent_status:
                    AnimatedMessageBox.showInformation(
                        self.window(),
                        "AI 功能已启用",
                        "AI 功能已启用。您现在可以使用 AI 电子宠物和智能报告功能。",
                    )
                else:
                    AnimatedMessageBox.showInformation(
                        self.window(),
                        "AI 功能已禁用",
                        "AI 功能已禁用。应用将不再发送数据至 AI 服务。",
                    )

                # Emit signal with the new status
                self.ai_consent_changed.emit(consent_status)
            else:
                logger.warning("AI consent update failed. Reverting checkbox state.")
                # Revert checkbox state
                self.ai_consent_checkbox.blockSignals(True)
                self.ai_consent_checkbox.setChecked(not consent_status)
                self.ai_consent_checkbox.blockSignals(False)
                AnimatedMessageBox.showWarning(
                    self.window(), "设置失败", "无法更新 AI 功能设置，请稍后重试。"
                )
        finally:
            # Ensure the flag is always reset, even if errors occur or returns happen early
            self._is_toggling_consent = False
            logger.debug("Reset _is_toggling_consent flag in finally block.")
