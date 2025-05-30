import logging
import sys
import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDialog,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QApplication,
)
from PySide6.QtCore import Slot, Qt, QTimer, QSize
from PySide6.QtGui import (
    QMovie,
    QPainter,
    QBitmap,
    QPainterPath,
    QIcon,
    QRegion,
)
from datetime import datetime

# Enhanced logging for debugging import issues
logger = logging.getLogger(__name__)
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"sys.path: {sys.path}")

# Try to import the AI handler function with better error handling
try:
    # First try relative import
    from ai_core.pet_handler import handle_pet_event, initialize_enhanced_dialogue

    logger.info(
        "Successfully imported handle_pet_event and initialize_enhanced_dialogue using relative import"
    )
except ImportError as e:
    logger.error(f"Failed to import handle_pet_event using relative import: {e}")

    # Try absolute import
    try:
        from kindness_companion_app.ai_core.pet_handler import (
            handle_pet_event,
            initialize_enhanced_dialogue,
        )

        logger.info(
            "Successfully imported handle_pet_event and initialize_enhanced_dialogue using absolute import"
        )
    except ImportError as e:
        logger.error(f"Failed to import handle_pet_event using absolute import: {e}")

        # Try to add parent directory to sys.path and retry
        try:
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                logger.info(f"Added {parent_dir} to sys.path")

            from ai_core.pet_handler import (
                handle_pet_event,
                initialize_enhanced_dialogue,
            )

            logger.info(
                "Successfully imported handle_pet_event and initialize_enhanced_dialogue after path adjustment"
            )
        except ImportError as e:
            logger.error(f"All import attempts failed: {e}")
            logger.error("AI pet features will be disabled.")
            handle_pet_event = None  # type: ignore
            initialize_enhanced_dialogue = None  # type: ignore

# Import UserManager
from kindness_companion_app.backend.user_manager import UserManager

logger = logging.getLogger(__name__)


class PetWidget(QWidget):
    def __init__(self, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.current_user = None
        self._pending_event = None
        self.movie = None  # Initialize movie attribute
        self.db_manager = None  # Will be set when database_manager is available
        self.chat_messages = (
            []
        )  # 存储聊天消息的列表，格式：[{'message': str, 'is_user': bool, 'timestamp': datetime}, ...]

        # Initialize enhanced dialogue generator if possible
        try:
            from kindness_companion_app.backend.database_manager import DatabaseManager

            self.db_manager = DatabaseManager()
            if initialize_enhanced_dialogue is not None:
                logger.info("Initializing enhanced dialogue generator")
                initialize_enhanced_dialogue(self.db_manager)
                logger.info("Enhanced dialogue generator initialized successfully")
            else:
                logger.warning(
                    "initialize_enhanced_dialogue is None, cannot initialize enhanced dialogue generator"
                )
        except Exception as e:
            logger.error(
                f"Error initializing enhanced dialogue generator: {e}", exc_info=True
            )

        self.setup_ui()
        self.connect_signals()  # 连接信号

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center content

        # Label to display the Pet Animation (GIF)
        self.pet_animation_label = QLabel()
        self.pet_animation_label.setObjectName("pet_animation_label")
        self.pet_animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_animation_label.setMinimumSize(QSize(200, 200))
        self.pet_animation_label.setFixedSize(200, 200)  # 保持正方形
        self.pet_animation_label.setScaledContents(False)  # 保持原始比例
        layout.addWidget(self.pet_animation_label)

        # Status Label
        self.pet_status_label = QLabel("你好！今天感觉怎么样？")
        self.pet_status_label.setObjectName("pet_status_label")
        self.pet_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pet_status_label)

        # 创建聊天记录显示区域
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("pet_chat_history")
        self.chat_history.setReadOnly(True)  # 设置为只读
        self.chat_history.setMinimumHeight(200)  # 设置最小高度
        self.chat_history.setMaximumHeight(300)  # 设置最大高度
        self.update_chat_history_style()  # 初始化样式
        layout.addWidget(self.chat_history)

        # Chat Input Area
        chat_layout = QHBoxLayout()
        chat_layout.setContentsMargins(10, 10, 10, 10)

        # Message input field
        self.message_input = QLineEdit()
        self.message_input.setObjectName("pet_message_input")
        self.message_input.setPlaceholderText("和宠物聊天...")
        self.message_input.setMinimumHeight(36)
        self.message_input.returnPressed.connect(self.send_message)

        # Send button
        self.send_button = QPushButton()
        self.send_button.setObjectName("pet_send_button")
        self.send_button.setIcon(QIcon(":/icons/send.png"))
        self.send_button.setFixedSize(28, 28)
        self.send_button.clicked.connect(self.send_message)

        # Add widgets to chat layout
        chat_layout.addWidget(self.message_input, 1)
        chat_layout.addWidget(self.send_button, 0)

        # Add chat layout to main layout
        layout.addLayout(chat_layout)

        self.setObjectName("pet_widget_area")

    def update_chat_history_style(self):
        """根据当前主题更新聊天历史框的样式"""
        app = QApplication.instance()
        theme_manager = None
        if app:
            theme_manager = app.property("theme_manager")
        theme = theme_manager.current_theme if theme_manager else "light"

        if theme == "dark":
            # 暗色主题样式
            self.chat_history.setStyleSheet(
                """
                QTextEdit {
                    background-color: #2D2D2D;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 14px;
                    color: #FFFFFF;
                }
                QTextEdit:disabled {
                    background-color: #1A1A1A;
                }
                QScrollBar:vertical {
                    background-color: #2D2D2D;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #404040;
                    min-height: 20px;
                    border-radius: 6px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """
            )
        else:
            # 亮色主题样式
            self.chat_history.setStyleSheet(
                """
                QTextEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 14px;
                    color: #333333;
                }
                QTextEdit:disabled {
                    background-color: #F5F5F5;
                }
                QScrollBar:vertical {
                    background-color: #F5F5F5;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #E0E0E0;
                    min-height: 20px;
                    border-radius: 6px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """
            )

    def resizeEvent(self, event):
        """Apply a circular mask whenever the widget is resized."""
        super().resizeEvent(event)
        rect = self.pet_animation_label.rect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            mask_region = QRegion(rect, QRegion.RegionType.Ellipse)
            self.pet_animation_label.setMask(mask_region)
        else:
            self.pet_animation_label.clearMask()

    @Slot(str, dict)
    def send_event_to_pet(self, event_type: str, event_data: dict):
        """Receives events from other parts of the app and triggers AI processing."""
        if not self.current_user:
            logger.warning("Cannot send event to pet: No user logged in.")
            return

        user_id = self.current_user.get("id")
        if not user_id:
            logger.error("Cannot send event to pet: User ID is missing.")
            return

        # --- AI Consent Check Removed ---
        # AI consent is now assumed True by default.
        logger.info(
            f"AI consent assumed True for user {user_id}. Proceeding with event: {event_type}"
        )
        self._call_ai_handler(user_id, event_type, event_data)
        # --- End AI Consent Check Removed ---

    def _call_ai_handler(self, user_id: int, event_type: str, event_data: dict):
        """Internal method to actually call the AI handler."""
        logger.info(
            f"Calling AI core: User {user_id}, Type: {event_type}, Data: {event_data}"
        )
        self.pet_status_label.setText("正在思考...")  # Changed thinking text

        # Check if handle_pet_event is available
        if handle_pet_event is None:
            logger.error("Cannot call AI handler: handle_pet_event is None")
            self.update_pet_display(
                {
                    "dialogue": "AI 功能未正确加载。请检查日志。",
                    "suggested_animation": "confused",
                }
            )
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
            self.update_pet_display(
                {"dialogue": "哎呀！好像出错了。", "suggested_animation": "confused"}
            )  # Example error state

    def add_message_to_history(self, message: str, is_user: bool = True):
        """添加消息到聊天历史记录"""
        if not message:
            return

        # 获取当前时间
        current_time = datetime.now()

        # 保存消息到列表
        self.chat_messages.append(
            {"message": message, "is_user": is_user, "timestamp": current_time}
        )

        # 渲染并添加消息到UI
        self._render_message_to_ui(message, is_user, current_time)

    def _render_message_to_ui(self, message: str, is_user: bool, timestamp: datetime):
        """将单条消息渲染到UI中"""
        # 格式化时间
        time_str = timestamp.strftime("%H:%M")

        # 获取当前主题
        app = QApplication.instance()
        theme_manager = None
        if app:
            theme_manager = app.property("theme_manager")
        theme = theme_manager.current_theme if theme_manager else "light"

        # 只设置文字颜色，不设置background-color，统一用QTextEdit的背景
        if theme == "dark":
            user_text_color = "#FFFFFF"
            ai_text_color = "#FFFFFF"
            time_color = "#B3B3B3"
        else:
            user_text_color = "#333333"
            ai_text_color = "#333333"
            time_color = "#666666"

        # 设置消息样式
        if is_user:
            message_html = f"""
                <div style='text-align: right; margin: 5px 0;'>
                    <span style='color: {user_text_color}; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; background: none;'>
                        {message}
                        <br>
                        <span style='font-size: 10px; color: {time_color};'>{time_str}</span>
                    </span>
                </div>
            """
        else:
            message_html = f"""
                <div style='text-align: left; margin: 5px 0;'>
                    <span style='color: {ai_text_color}; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; background: none;'>
                        {message}
                        <br>
                        <span style='font-size: 10px; color: {time_color};'>{time_str}</span>
                    </span>
                </div>
            """

        # 添加消息到聊天历史
        self.chat_history.append(message_html)
        # 滚动到底部
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def _rerender_all_messages(self):
        """重新渲染所有聊天消息（用于主题切换）"""
        # 清空聊天历史显示
        self.chat_history.clear()

        # 重新渲染所有保存的消息
        for msg_data in self.chat_messages:
            self._render_message_to_ui(
                msg_data["message"], msg_data["is_user"], msg_data["timestamp"]
            )

    def update_pet_display(self, response: dict):
        """Updates the pet animation GIF and dialogue bubble."""
        dialogue = response.get("dialogue", "")
        suggested_animation = response.get("suggested_animation", "idle")
        logger.info(
            f"Updating pet display. Animation: {suggested_animation}, Dialogue: '{dialogue[:20]}...'"
        )

        # 添加AI回复到聊天历史
        if dialogue:
            self.add_message_to_history(dialogue, is_user=False)

        # --- Update Status Label Text based on animation ---
        # 检查是否有智能生成的状态文字
        smart_status_text = response.get("smart_status_text", "")

        if smart_status_text:
            # 使用智能生成的状态文字
            status_text = smart_status_text
        else:
            # 回退到原有的简单映射
            status_text_map = {
                "idle": "我在这里陪着你呢~",
                "happy": "看起来很开心！",
                "excited": "好兴奋呀！",
                "concerned": "有点担心...",
                "confused": "嗯？怎么了？",
                "thinking": "让我想想...",
                # Add emotion-specific status texts
                "sad": "看起来有点难过...",
                "anxious": "似乎有些焦虑...",
                "worried": "好像在担心什么...",
                "frustrated": "看起来有点沮丧...",
                "angry": "似乎有些生气...",
                "disappointed": "看起来有点失望...",
                "stressed": "好像压力有点大...",
                "calm": "看起来很平静...",
                "reflective": "正在思考...",
                "curious": "好奇地看着你...",
                "surprised": "看起来很惊讶！",
                "uncertain": "似乎有些犹豫...",
            }

            # Get emotion from response if available
            emotion = response.get("emotion_detected", "")

            # First try to get status text based on emotion
            if emotion and emotion in status_text_map:
                status_text = status_text_map[emotion]
            # Otherwise use animation
            else:
                status_text = status_text_map.get(
                    suggested_animation, "我在这里陪着你呢~"
                )

        self.pet_status_label.setText(status_text)

        # --- Update Animation GIF ---
        gif_path = f":/animations/{suggested_animation}.gif"
        logger.debug(f"Attempting to load animation from: {gif_path}")

        # Stop the current movie if it's running
        if self.movie and self.movie.state() == QMovie.MovieState.Running:
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
                size_valid = (
                    label_size.isValid()
                    and label_size.width() > 0
                    and label_size.height() > 0
                )
                logger.debug(
                    f"apply_scaling_and_mask called. Label size: {label_size.width()}x{label_size.height()}, Is valid: {size_valid}"
                )

                if size_valid:
                    logger.debug(
                        f"Label size valid. Scaling movie to {label_size.width()}x{label_size.height()} and applying mask."
                    )
                    if self.movie is not None:
                        self.movie.setScaledSize(label_size)
                        self.resizeEvent(None)  # Force mask update using current size
                        logger.debug("Starting movie...")
                        self.movie.start()
                        logger.debug(
                            f"Movie state after start(): {self.movie.state()}"
                        )  # Log state after starting
                else:
                    # If size is still not valid, try again slightly later
                    logger.warning(
                        "Label size not valid yet. Retrying mask/scale shortly."
                    )
                    QTimer.singleShot(50, apply_scaling_and_mask)

            # Start the process, potentially deferred if size isn't ready
            logger.debug("Initiating apply_scaling_and_mask.")
            apply_scaling_and_mask()
            # --- Ensure label has size before scaling and applying mask --- END

        else:
            logger.warning(
                f"Failed to load animation: {gif_path}. Displaying fallback text."
            )
            self.pet_animation_label.clear()  # Clear any previous movie
            self.pet_animation_label.setText("🐾")  # Set fallback text
            self.pet_animation_label.clearMask()  # Clear mask if animation failed

    def send_message(self):
        """Handles sending a user message to the pet."""
        if not self.current_user:
            # Use standard QMessageBox instead of AnimatedMessageBox
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "无法发送", "请先登录。")
            return

        user_message = self.message_input.text().strip()
        if not user_message:
            return

        user_id = self.current_user.get("id")

        # --- AI Consent Check Removed ---
        logger.info(
            f"AI consent assumed True for user {user_id}. Proceeding with sending message."
        )
        # --- End AI Consent Check Removed ---

        # 添加用户消息到聊天历史
        self.add_message_to_history(user_message, is_user=True)

        # Clear input and show thinking state
        self.message_input.clear()
        self.pet_status_label.setText("正在思考...")

        # Prepare event data
        event_data = {"message": user_message}

        if user_id is not None:
            self._call_ai_handler(user_id, "user_message", event_data)

    @Slot(dict)
    def set_user(self, user: dict | None):
        """Sets the current user and initializes/clears pet state."""
        self.current_user = user
        if user:
            user_id = user.get("id")
            logger.info(f"PetWidget set user: {user_id}")

            # --- AI Consent Check Removed ---
            # Always enable UI elements if user is logged in
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.pet_status_label.setText("你好！今天感觉怎么样？")
            # Load initial pet state or default animation
            self.update_pet_display(
                {"dialogue": "你好！很高兴见到你！", "suggested_animation": "idle"}
            )
            logger.info(f"AI consent assumed True for user {user_id}. Pet UI enabled.")
            # --- End AI Consent Check Removed ---

        else:
            logger.info("PetWidget user set to None (logged out).")
            # Clear pet state and hide UI elements
            self.pet_animation_label.clear()
            self.pet_status_label.setText("请先登录")
            self.message_input.clear()
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.chat_history.clear()  # 清空聊天历史
            self.chat_messages.clear()  # 清空聊天消息存储

    @Slot(str, str)
    def handle_theme_changed(self, theme_type: str, theme_style: str):
        """处理主题变更事件"""
        logger.info(f"Theme changed to: {theme_type}, style: {theme_style}")

        # 更新聊天历史样式
        self.update_chat_history_style()

        # 重新渲染所有消息以应用新的主题颜色
        self._rerender_all_messages()

        logger.info("Chat history style updated for theme change")

    def connect_signals(self):
        """连接信号"""
        # 连接主题变更信号
        app = QApplication.instance()
        if app:
            theme_manager = app.property("theme_manager")
            if theme_manager and hasattr(theme_manager, "theme_changed"):
                theme_manager.theme_changed.connect(self.handle_theme_changed)
                logger.info("Successfully connected to theme_changed signal")
            else:
                logger.warning("Theme manager or theme_changed signal not available")
