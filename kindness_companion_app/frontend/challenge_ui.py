from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QMessageBox, QGridLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QFontMetrics
import datetime

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox


class ChallengeCard(QFrame):
    """
    Widget for displaying a single challenge.
    """

    # Signals
    subscribe_clicked = Signal(int)  # Challenge ID
    unsubscribe_clicked = Signal(int)  # Challenge ID
    check_in_clicked = Signal(int)  # Challenge ID

    def __init__(self, challenge, is_subscribed=False, streak=0):
        """
        Initialize the challenge card.

        Args:
            challenge (dict): Challenge information
            is_subscribed (bool): Whether the user is subscribed to this challenge
            streak (int): Current streak for this challenge
        """
        super().__init__()

        self.challenge = challenge
        self.is_subscribed = is_subscribed
        self.streak = streak

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Set frame style and object name
        self.setObjectName("challenge_card")  # Set object name for styling
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)  # Keep shadow for card effect
        self.setLineWidth(1)

        # 设置卡片的最小高度，确保卡片有足够的空间
        self.setMinimumHeight(200)

        # 设置卡片的大小策略，使其在垂直方向上可以扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)  # 增加内边距
        self.main_layout.setSpacing(12)  # 增加元素间距

        # Title
        self.title_label = QLabel(self.challenge["title"])
        self.title_label.setObjectName("challenge_title_label")  # 使用特定的对象名

        # 设置标题字体
        title_font = QFont("Hiragino Sans GB", 18, QFont.Bold)
        self.title_label.setFont(title_font)

        self.main_layout.addWidget(self.title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("background-color: #EAEAEA;")
        self.main_layout.addWidget(separator)

        # Description
        self.description_label = QLabel(self.challenge["description"])
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("challenge_description_label")

        # 设置描述文本的最小高度，确保有足够的空间
        self.description_label.setMinimumHeight(60)

        self.main_layout.addWidget(self.description_label)
        self.main_layout.addSpacing(10)  # 添加额外的空间

        # Metadata layout
        self.meta_layout = QHBoxLayout()
        self.meta_layout.setSpacing(15)  # 增加元素间距

        # Category
        self.category_label = QLabel(f"分类: {self.challenge['category']}")
        self.category_label.setObjectName("challenge_category_label")
        self.meta_layout.addWidget(self.category_label)

        # Difficulty
        difficulty_text = "★" * self.challenge["difficulty"]
        self.difficulty_label = QLabel(f"难度: {difficulty_text}")
        self.difficulty_label.setObjectName("challenge_difficulty_label")
        self.meta_layout.addWidget(self.difficulty_label)

        # --- Add streak label placeholder (always present, visibility toggled) ---
        self.streak_label = QLabel("") # Create label, initially empty
        self.streak_label.setObjectName("streak_label")
        self.streak_label.setVisible(False) # Initially hidden

        # 设置连续打卡标签的字体
        streak_font = QFont("Hiragino Sans GB", 16, QFont.Bold)
        self.streak_label.setFont(streak_font)

        self.meta_layout.addWidget(self.streak_label)

        # 添加弹性空间，使连续打卡标签靠右对齐
        self.meta_layout.addStretch()

        self.main_layout.addLayout(self.meta_layout)

        # 添加分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setLineWidth(1)
        separator2.setStyleSheet("background-color: #EAEAEA;")
        self.main_layout.addWidget(separator2)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignRight)
        self.button_layout.setSpacing(10)  # 增加按钮间距
        self.button_layout.setContentsMargins(0, 10, 0, 0)  # 添加上边距

        # --- Create buttons but don't add them yet ---
        self.icon_size = QSize(20, 20)  # 增加图标尺寸

        self.subscribe_button = QPushButton("订阅挑战")
        self.subscribe_button.setObjectName("subscribe_button")
        self.subscribe_button.setIcon(QIcon(":/icons/plus-circle.svg"))
        self.subscribe_button.setIconSize(self.icon_size)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.subscribe_button.font())
        text_width = font_metrics.horizontalAdvance("订阅挑战") + 40  # 文本宽度加上一些额外空间
        self.subscribe_button.setMinimumWidth(max(120, text_width))  # 确保最小宽度足够
        self.subscribe_button.setMinimumHeight(font_metrics.height() * 2)  # 高度为字体高度的2倍
        self.subscribe_button.clicked.connect(
            lambda: self.subscribe_clicked.emit(self.challenge["id"])
        )

        self.unsubscribe_button = QPushButton("取消订阅")
        self.unsubscribe_button.setObjectName("unsubscribe_button")
        self.unsubscribe_button.setIcon(QIcon(":/icons/x-circle.svg"))
        self.unsubscribe_button.setIconSize(self.icon_size)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.unsubscribe_button.font())
        text_width = font_metrics.horizontalAdvance("取消订阅") + 40  # 文本宽度加上一些额外空间
        self.unsubscribe_button.setMinimumWidth(max(120, text_width))  # 确保最小宽度足够
        self.unsubscribe_button.setMinimumHeight(font_metrics.height() * 2)  # 高度为字体高度的2倍
        self.unsubscribe_button.clicked.connect(
            lambda: self.unsubscribe_clicked.emit(self.challenge["id"])
        )

        self.check_in_button = QPushButton("今日打卡")
        self.check_in_button.setObjectName("check_in_button")
        self.check_in_button.setIcon(QIcon(":/icons/check-square.svg"))
        self.check_in_button.setIconSize(self.icon_size)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.check_in_button.font())
        text_width = font_metrics.horizontalAdvance("今日打卡") + 40  # 文本宽度加上一些额外空间
        self.check_in_button.setMinimumWidth(max(120, text_width))  # 确保最小宽度足够
        self.check_in_button.setMinimumHeight(font_metrics.height() * 2)  # 高度为字体高度的2倍
        # 设置打卡按钮为主要按钮样式
        self.check_in_button.setProperty("class", "primaryButton")
        self.check_in_button.clicked.connect(
            lambda: self.check_in_clicked.emit(self.challenge["id"])
        )

        # --- Add button layout to main layout ---
        self.main_layout.addLayout(self.button_layout)

        # --- Initial UI update based on initial state ---
        self._update_card_elements()

    def update_ui(self, is_subscribed, streak):
        """Updates the card's UI elements based on subscription and streak."""
        self.is_subscribed = is_subscribed
        self.streak = streak
        self._update_card_elements()

    def _update_card_elements(self):
        """Helper method to update streak label and buttons."""
        # --- Update Streak Label ---
        if self.is_subscribed and self.streak > 0:
            self.streak_label.setText(f"连续打卡: {self.streak}天")
            self.streak_label.setVisible(True)
        else:
            self.streak_label.setText("") # Clear text
            self.streak_label.setVisible(False)

        # --- Update Buttons ---
        # Clear existing buttons from layout first
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None) # Remove widget from layout

        # Add buttons based on subscription status
        if self.is_subscribed:
            self.button_layout.addWidget(self.check_in_button)
            self.button_layout.addWidget(self.unsubscribe_button)
        else:
            self.button_layout.addWidget(self.subscribe_button)


class ChallengeListWidget(QWidget):
    """
    Widget for displaying and managing challenges.
    """

    def __init__(self, challenge_manager, progress_tracker):
        """
        Initialize the challenge list widget.

        Args:
            challenge_manager: Challenge manager instance
            progress_tracker: Progress tracker instance
        """
        super().__init__()

        self.challenge_manager = challenge_manager
        self.progress_tracker = progress_tracker
        self.current_user = None
        self.challenge_cards = {}  # Dictionary to store challenge cards by ID

        # 设置窗口大小变化时的响应
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_layout)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)  # 增加内边距
        self.main_layout.setSpacing(20)  # 增加元素间距

        # Header layout
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 15)  # 添加底部边距

        # Title
        self.title_label = QLabel("善行挑战列表")
        self.title_label.setObjectName("title_label")  # Set object name for styling

        # 设置标题字体
        title_font = QFont("Hiragino Sans GB", 22, QFont.Bold)
        self.title_label.setFont(title_font)

        self.header_layout.addWidget(self.title_label)

        # Filter layout
        self.filter_layout = QHBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignRight)
        self.filter_layout.setSpacing(15)  # 增加过滤器间距

        # Category filter
        self.category_label = QLabel("分类:")
        self.category_label.setObjectName("filter_label")  # 设置对象名，便于样式表定制
        self.category_combo = QComboBox()
        self.category_combo.setObjectName("filter_combo")  # 设置对象名，便于样式表定制
        self.category_combo.addItem("全部分类", None)
        self.category_combo.currentIndexChanged.connect(self.filter_challenges)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.category_combo.font())
        self.category_combo.setMinimumWidth(font_metrics.horizontalAdvance("全部分类XXXXX"))  # 确保足够宽度显示内容
        self.category_combo.setMinimumHeight(font_metrics.height() * 2.2)  # 高度为字体高度的2.2倍
        self.category_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.filter_layout.addWidget(self.category_label)
        self.filter_layout.addWidget(self.category_combo)

        # Difficulty filter
        self.difficulty_label = QLabel("难度:")
        self.difficulty_label.setObjectName("filter_label")  # 设置对象名，便于样式表定制
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.setObjectName("filter_combo")  # 设置对象名，便于样式表定制
        self.difficulty_combo.addItem("全部难度", None)
        for i in range(1, 6):
            self.difficulty_combo.addItem("★" * i, i)
        self.difficulty_combo.currentIndexChanged.connect(self.filter_challenges)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.difficulty_combo.font())
        self.difficulty_combo.setMinimumWidth(font_metrics.horizontalAdvance("全部难度★★★★★"))  # 确保足够宽度显示内容
        self.difficulty_combo.setMinimumHeight(font_metrics.height() * 2.2)  # 高度为字体高度的2.2倍
        self.difficulty_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.filter_layout.addWidget(self.difficulty_label)
        self.filter_layout.addWidget(self.difficulty_combo)

        # Subscription filter
        self.subscription_label = QLabel("订阅:")
        self.subscription_label.setObjectName("filter_label")  # 设置对象名，便于样式表定制
        self.subscription_combo = QComboBox()
        self.subscription_combo.setObjectName("filter_combo")  # 设置对象名，便于样式表定制
        self.subscription_combo.addItem("全部挑战", None)
        self.subscription_combo.addItem("已订阅", True)
        self.subscription_combo.addItem("未订阅", False)
        self.subscription_combo.currentIndexChanged.connect(self.filter_challenges)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.subscription_combo.font())
        self.subscription_combo.setMinimumWidth(font_metrics.horizontalAdvance("全部挑战XXXXX"))  # 确保足够宽度显示内容
        self.subscription_combo.setMinimumHeight(font_metrics.height() * 2.2)  # 高度为字体高度的2.2倍
        self.subscription_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.filter_layout.addWidget(self.subscription_label)
        self.filter_layout.addWidget(self.subscription_combo)

        self.header_layout.addLayout(self.filter_layout)
        self.main_layout.addLayout(self.header_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("background-color: #EAEAEA;")
        self.main_layout.addWidget(separator)

        # Scroll area for challenges
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setObjectName("challenges_scroll_area")  # 设置对象名，便于样式表定制

        # Container widget for challenges
        self.challenges_widget = QWidget()
        self.challenges_widget.setObjectName("challenges_container")  # 设置对象名，便于样式表定制
        self.challenges_layout = QGridLayout(self.challenges_widget)
        self.challenges_layout.setContentsMargins(5, 10, 5, 10)  # 调整内边距
        self.challenges_layout.setSpacing(20)  # 增加卡片间距
        self.challenges_layout.setAlignment(Qt.AlignTop)  # 确保卡片从顶部开始排列

        self.scroll_area.setWidget(self.challenges_widget)
        self.main_layout.addWidget(self.scroll_area)

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information
        """
        self.current_user = user

        if user:
            # Load challenges
            self.load_challenges()
            self.load_categories()
        else:
            # Clear challenges
            self.clear_challenges()

    def load_categories(self):
        """Load challenge categories."""
        # Get all challenges
        challenges = self.challenge_manager.get_all_challenges()

        # Extract unique categories
        categories = set()
        for challenge in challenges:
            categories.add(challenge["category"])

        # Clear and repopulate category combo
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", None)
        for category in sorted(categories):
            self.category_combo.addItem(category, category)

    def load_challenges(self):
        """Load and display challenges."""
        if not self.current_user:
            return

        # Clear existing challenges
        self.clear_challenges()

        # Get all challenges
        challenges = self.challenge_manager.get_all_challenges()

        # Get user subscriptions
        user_challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])
        subscribed_ids = {challenge["id"] for challenge in user_challenges}

        # Get streaks for subscribed challenges
        streaks = {}
        for challenge_id in subscribed_ids:
            streaks[challenge_id] = self.progress_tracker.get_streak(
                self.current_user["id"], challenge_id
            )

        # Create challenge cards
        row, col = 0, 0

        # 根据容器宽度动态确定列数
        container_width = self.challenges_widget.width()
        if container_width < 600:
            max_cols = 1  # 窄容器只显示一列
        else:
            max_cols = 2  # 宽容器显示两列

        for challenge in challenges:
            is_subscribed = challenge["id"] in subscribed_ids
            streak = streaks.get(challenge["id"], 0) if is_subscribed else 0

            # Check if card already exists (e.g., after filter change)
            if challenge["id"] in self.challenge_cards:
                card = self.challenge_cards[challenge["id"]]
                # Update existing card's data and UI (important for filters)
                card.update_ui(is_subscribed, streak)
            else:
                # Create new card
                card = ChallengeCard(challenge, is_subscribed, streak)
                card.subscribe_clicked.connect(self.subscribe_to_challenge)
                card.unsubscribe_clicked.connect(self.unsubscribe_from_challenge)
                card.check_in_clicked.connect(self.check_in_challenge)
                self.challenge_cards[challenge["id"]] = card

            # Add card to layout (might be re-adding if it existed)
            # Ensure it's added correctly to the grid
            # Check if widget is already in the layout to avoid issues
            if self.challenges_layout.indexOf(card) == -1:
                 self.challenges_layout.addWidget(card, row, col)
            else: # If already in layout, ensure its position is correct (might not be needed if grid handles it)
                 pass # Assume grid layout handles existing widgets correctly

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Apply filters after loading/updating all cards
        self.filter_challenges()

    def filter_challenges(self):
        """Filter challenges based on selected criteria."""
        if not self.current_user:
            return

        # Get filter values
        category = self.category_combo.currentData()
        difficulty = self.difficulty_combo.currentData()
        subscription = self.subscription_combo.currentData()

        # Show/hide challenge cards based on filters
        for challenge_id, card in self.challenge_cards.items():
            challenge = card.challenge
            is_subscribed = card.is_subscribed

            # Apply filters
            show = True

            if category is not None and challenge["category"] != category:
                show = False

            if difficulty is not None and challenge["difficulty"] != difficulty:
                show = False

            if subscription is not None and is_subscribed != subscription:
                show = False

            # Show or hide the card
            card.setVisible(show)

    def clear_challenges(self):
        """Clear all challenge cards."""
        # Remove all widgets from the layout
        while self.challenges_layout.count():
            item = self.challenges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear the dictionary
        self.challenge_cards.clear()

    def subscribe_to_challenge(self, challenge_id):
        """
        Subscribe to a challenge.

        Args:
            challenge_id (int): Challenge ID
        """
        if not self.current_user:
            return

        success = self.challenge_manager.subscribe_to_challenge(
            self.current_user["id"], challenge_id
        )

        if success:
            # --- Update the specific challenge card ---
            if challenge_id in self.challenge_cards:
                card = self.challenge_cards[challenge_id]
                card.update_ui(is_subscribed=True, streak=0) # Update UI directly

            # Show success message non-modally using AnimatedMessageBox
            challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
            subscribe_success_msg = AnimatedMessageBox(self) # Use AnimatedMessageBox
            subscribe_success_msg.setWindowTitle("订阅成功")
            subscribe_success_msg.setText(f"您已成功订阅{challenge['title']}挑战！\n记得每天完成挑战并打卡哦。")
            subscribe_success_msg.setIcon(QMessageBox.Information)
            subscribe_success_msg.showNonModal() # Use custom non-modal method

    def unsubscribe_from_challenge(self, challenge_id):
        """
        Unsubscribe from a challenge.

        Args:
            challenge_id (int): Challenge ID
        """
        if not self.current_user:
            return

        # Ask for confirmation using AnimatedMessageBox
        challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
            self,
            "取消订阅",
            f"确定要取消订阅{challenge['title']}挑战吗？\n"
            f"您的打卡记录将会保留，但连续打卡天数会重置。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.challenge_manager.unsubscribe_from_challenge(
                self.current_user["id"], challenge_id
            )

            if success:
                # --- Update the specific challenge card ---
                if challenge_id in self.challenge_cards:
                    card = self.challenge_cards[challenge_id]
                    card.update_ui(is_subscribed=False, streak=0) # Update UI directly

    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        # 使用计时器延迟执行布局调整，避免频繁调整
        self.resize_timer.start(200)  # 200毫秒后执行布局调整

    def adjust_layout(self):
        """根据容器宽度调整布局"""
        if not self.challenge_cards:
            return

        # 根据容器宽度动态确定列数
        container_width = self.challenges_widget.width()
        if container_width < 600:
            max_cols = 1  # 窄容器只显示一列
        else:
            max_cols = 2  # 宽容器显示两列

        # 重新布局挑战卡片
        row, col = 0, 0
        for card_id, card in self.challenge_cards.items():
            if card.isVisible():
                # 先从布局中移除
                self.challenges_layout.removeWidget(card)
                # 再添加到新位置
                self.challenges_layout.addWidget(card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def check_in_challenge(self, challenge_id):
        """
        Check in for a challenge.

        Args:
            challenge_id (int): Challenge ID
        """
        if not self.current_user:
            return

        # Check if already checked in today
        today = datetime.date.today().isoformat()
        check_ins = self.progress_tracker.get_check_ins(
            self.current_user["id"], challenge_id, today, today
        )

        if check_ins:
            # Show already checked-in message non-modally using AnimatedMessageBox
            already_checked_msg = AnimatedMessageBox(self) # Use AnimatedMessageBox
            already_checked_msg.setWindowTitle("已打卡")
            already_checked_msg.setText("您今天已经完成了这个挑战的打卡！\n明天再来继续保持吧。")
            already_checked_msg.setIcon(QMessageBox.Information)
            already_checked_msg.showNonModal() # Use custom non-modal method
            return

        # Ask for confirmation using AnimatedMessageBox
        challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
            self,
            "打卡确认",
            f"确认您今天已完成{challenge['title']}挑战吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Perform check-in and show success message (potentially delayed)
            success = self.progress_tracker.check_in(
                self.current_user["id"], challenge_id
            )

            if success:
                # Update streak
                streak = self.progress_tracker.get_streak(
                    self.current_user["id"], challenge_id
                )

                # --- Update the specific challenge card ---
                if challenge_id in self.challenge_cards:
                    card = self.challenge_cards[challenge_id]
                    # Pass the newly calculated streak
                    card.update_ui(is_subscribed=True, streak=streak)

                # Show success message non-modally using AnimatedMessageBox
                checkin_success_msg = AnimatedMessageBox(self) # Use AnimatedMessageBox
                checkin_success_msg.setWindowTitle("打卡成功")
                checkin_success_msg.setText(f"恭喜您完成今日{challenge['title']}挑战！\n您已连续打卡 {streak} 天。")
                checkin_success_msg.setIcon(QMessageBox.Information)
                checkin_success_msg.showNonModal() # Use custom non-modal method
