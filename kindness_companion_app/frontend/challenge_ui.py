from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QComboBox,
    QMessageBox,
    QGridLayout,
    QSizePolicy,
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
        self.setObjectName("challenge_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)

        # 优化卡片尺寸和布局
        self.setMinimumHeight(200)  # 增加最小高度
        self.setMaximumHeight(350)  # 增加最大高度
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)  # 增加内边距
        self.main_layout.setSpacing(12)  # 增加元素间距

        # Title
        self.title_label = QLabel(self.challenge["title"])
        self.title_label.setObjectName("challenge_title_label")
        self.title_label.setWordWrap(True)
        self.title_label.setMinimumHeight(45)  # 增加标题高度
        self.title_label.setToolTip(self.challenge["title"])
        self.title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        title_font = QFont("Hiragino Sans GB", 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.main_layout.addWidget(self.title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        self.main_layout.addWidget(separator)

        # Description
        self.description_label = QLabel(self.challenge["description"])
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("challenge_description_label")
        self.description_label.setMinimumHeight(60)  # 增加描述高度
        self.description_label.setMaximumHeight(100)  # 增加最大高度
        self.description_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.description_label.setToolTip(self.challenge["description"])
        self.description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.main_layout.addWidget(self.description_label)
        self.main_layout.addSpacing(8)  # 增加间距

        # Metadata layout
        self.meta_layout = QHBoxLayout()
        self.meta_layout.setSpacing(12)  # 增加间距

        # 分类
        self.category_box = QFrame()
        self.category_box.setObjectName("challenge_meta_box")
        category_layout = QVBoxLayout(self.category_box)
        category_layout.setContentsMargins(8, 8, 8, 8)
        category_layout.setSpacing(2)
        category_label = QLabel("分类:")
        category_label.setObjectName("challenge_meta_label")
        category_value = QLabel(self.challenge["category"])
        category_value.setObjectName("challenge_meta_value")
        category_value.setWordWrap(True)
        category_layout.addWidget(category_label)
        category_layout.addWidget(category_value)
        self.meta_layout.addWidget(self.category_box)

        # 难度
        self.difficulty_box = QFrame()
        self.difficulty_box.setObjectName("challenge_meta_box")
        difficulty_layout = QVBoxLayout(self.difficulty_box)
        difficulty_layout.setContentsMargins(8, 8, 8, 8)
        difficulty_layout.setSpacing(2)
        difficulty_label = QLabel("难度:")
        difficulty_label.setObjectName("challenge_meta_label")
        difficulty_value = QLabel("★" * self.challenge["difficulty"])
        difficulty_value.setObjectName("challenge_meta_value")
        difficulty_layout.addWidget(difficulty_label)
        difficulty_layout.addWidget(difficulty_value)
        self.meta_layout.addWidget(self.difficulty_box)

        # 连续打卡
        self.streak_box = QFrame()
        self.streak_box.setObjectName("challenge_meta_box")
        streak_layout = QVBoxLayout(self.streak_box)
        streak_layout.setContentsMargins(8, 8, 8, 8)
        streak_layout.setSpacing(2)
        streak_label = QLabel("连续打卡:")
        streak_label.setObjectName("challenge_meta_label")
        self.streak_value = QLabel(f"{self.streak}天")
        self.streak_value.setObjectName("challenge_meta_value")
        streak_layout.addWidget(streak_label)
        streak_layout.addWidget(self.streak_value)
        self.meta_layout.addWidget(self.streak_box)

        # 添加弹性空间
        self.meta_layout.addStretch()

        self.main_layout.addLayout(self.meta_layout)

        # 添加分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setLineWidth(1)
        self.main_layout.addWidget(separator2)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.button_layout.setSpacing(10)  # 增加按钮间距
        self.button_layout.setContentsMargins(0, 10, 0, 0)  # 增加上边距

        # 设置按钮样式
        self.icon_size = QSize(20, 20)  # 增加图标尺寸
        button_min_width = 100  # 增加按钮最小宽度
        button_min_height = 30  # 增加按钮最小高度

        # Subscribe button
        self.subscribe_button = QPushButton("订阅挑战")
        self.subscribe_button.setObjectName("subscribe_button")
        self.subscribe_button.setIcon(QIcon(":/icons/plus-circle.svg"))
        self.subscribe_button.setIconSize(self.icon_size)
        self.subscribe_button.setMinimumWidth(button_min_width)
        self.subscribe_button.setMinimumHeight(button_min_height)
        self.subscribe_button.clicked.connect(
            lambda: self.subscribe_clicked.emit(self.challenge["id"])
        )

        # Unsubscribe button
        self.unsubscribe_button = QPushButton("取消订阅")
        self.unsubscribe_button.setObjectName("unsubscribe_button")
        self.unsubscribe_button.setIcon(QIcon(":/icons/x-circle.svg"))
        self.unsubscribe_button.setIconSize(self.icon_size)
        self.unsubscribe_button.setMinimumWidth(button_min_width)
        self.unsubscribe_button.setMinimumHeight(button_min_height)
        self.unsubscribe_button.clicked.connect(
            lambda: self.unsubscribe_clicked.emit(self.challenge["id"])
        )

        # Check-in button
        self.check_in_button = QPushButton("今日打卡")
        self.check_in_button.setObjectName("check_in_button")
        self.check_in_button.setIcon(QIcon(":/icons/check-square.svg"))
        self.check_in_button.setIconSize(self.icon_size)
        self.check_in_button.setMinimumWidth(button_min_width)
        self.check_in_button.setMinimumHeight(button_min_height)
        self.check_in_button.setProperty("class", "primaryButton")
        self.check_in_button.clicked.connect(
            lambda: self.check_in_clicked.emit(self.challenge["id"])
        )

        # Add buttons to layout
        self.button_layout.addWidget(self.subscribe_button)
        self.button_layout.addWidget(self.unsubscribe_button)
        self.button_layout.addWidget(self.check_in_button)

        self.main_layout.addLayout(self.button_layout)

        # --- Initial UI update based on initial state ---
        self._update_card_elements()

    def update_ui(self, is_subscribed, streak):
        """Updates the card's UI elements based on subscription and streak."""
        self.is_subscribed = is_subscribed
        self.streak = streak
        # 更新嵌套布局中的内容
        category_value_label = self.category_box.findChild(
            QLabel, "challenge_meta_value"
        )
        if category_value_label is not None:
            category_value_label.setText(self.challenge["category"])
        difficulty_value_label = self.difficulty_box.findChild(
            QLabel, "challenge_meta_value"
        )
        if difficulty_value_label is not None:
            difficulty_value_label.setText("★" * self.challenge["difficulty"])
        self.streak_value.setText(f"{self.streak}天")
        self._update_card_elements()

    def _update_card_elements(self):
        """Helper method to update streak label and buttons."""
        # --- Update Streak Label ---
        if self.is_subscribed and self.streak > 0:
            self.streak_value.setText(f"{self.streak}天")
        else:
            self.streak_value.setText("")  # Clear text

        # --- Update Buttons ---
        # Clear existing buttons from layout first
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # Remove widget from layout

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

    # 新增信号，订阅/取消订阅后发射
    challenge_subscription_changed = Signal()

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
        self.title_label = QLabel("善行伴侣列表")
        self.title_label.setObjectName("title_label")  # Set object name for styling

        # 设置标题字体
        title_font = QFont("Hiragino Sans GB", 22, QFont.Weight.Bold)
        self.title_label.setFont(title_font)

        self.header_layout.addWidget(self.title_label)

        # Filter layout
        self.filter_layout = QHBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
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
        self.category_combo.setMinimumWidth(
            font_metrics.horizontalAdvance("全部分类XXXXX")
        )  # 确保足够宽度显示内容
        self.category_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.category_combo.setMinimumHeight(int(font_metrics.height() * 2.2))
        self.filter_layout.addWidget(self.category_label)
        self.filter_layout.addWidget(self.category_combo)

        # Difficulty filter
        self.difficulty_label = QLabel("难度:")
        self.difficulty_label.setObjectName(
            "filter_label"
        )  # 设置对象名，便于样式表定制
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.setObjectName(
            "filter_combo"
        )  # 设置对象名，便于样式表定制
        self.difficulty_combo.addItem("全部难度", None)
        for i in range(1, 6):
            self.difficulty_combo.addItem("★" * i, i)
        self.difficulty_combo.currentIndexChanged.connect(self.filter_challenges)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.difficulty_combo.font())
        self.difficulty_combo.setMinimumWidth(
            font_metrics.horizontalAdvance("全部难度★★★★★")
        )  # 确保足够宽度显示内容
        self.difficulty_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.difficulty_combo.setMinimumHeight(int(font_metrics.height() * 2.2))
        self.filter_layout.addWidget(self.difficulty_label)
        self.filter_layout.addWidget(self.difficulty_combo)

        # Subscription filter
        self.subscription_label = QLabel("订阅:")
        self.subscription_label.setObjectName(
            "filter_label"
        )  # 设置对象名，便于样式表定制
        self.subscription_combo = QComboBox()
        self.subscription_combo.setObjectName(
            "filter_combo"
        )  # 设置对象名，便于样式表定制
        self.subscription_combo.addItem("全部挑战", None)
        self.subscription_combo.addItem("已订阅", True)
        self.subscription_combo.addItem("未订阅", False)
        self.subscription_combo.currentIndexChanged.connect(self.filter_challenges)
        # 使用相对尺寸，基于字体大小
        font_metrics = QFontMetrics(self.subscription_combo.font())
        self.subscription_combo.setMinimumWidth(
            font_metrics.horizontalAdvance("全部挑战XXXXX")
        )  # 确保足够宽度显示内容
        self.subscription_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.subscription_combo.setMinimumHeight(int(font_metrics.height() * 2.2))
        self.filter_layout.addWidget(self.subscription_label)
        self.filter_layout.addWidget(self.subscription_combo)

        self.header_layout.addLayout(self.filter_layout)
        self.main_layout.addLayout(self.header_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        self.main_layout.addWidget(separator)

        # Scroll area for challenges
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setObjectName(
            "challenges_scroll_area"
        )  # 设置对象名，便于样式表定制

        # Container widget for challenges
        self.challenges_widget = QWidget()
        self.challenges_widget.setObjectName(
            "challenges_container"
        )  # 设置对象名，便于样式表定制
        self.challenges_layout = QGridLayout(self.challenges_widget)
        self.challenges_layout.setContentsMargins(5, 10, 5, 10)  # 调整内边距
        self.challenges_layout.setSpacing(20)  # 增加卡片间距
        self.challenges_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )  # 确保卡片从顶部开始排列

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
        # Get unique categories from the backend (more efficient and consistent)
        categories = self.challenge_manager.get_unique_categories()

        # Clear and repopulate category combo
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", None)
        for category in categories:  # Categories are already sorted by backend
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
        user_challenges = self.challenge_manager.get_user_challenges(
            self.current_user["id"]
        )
        subscribed_ids = {challenge["id"] for challenge in user_challenges}

        # Get streaks for subscribed challenges
        streaks = {}
        for challenge_id in subscribed_ids:
            streaks[challenge_id] = self.progress_tracker.get_streak(
                self.current_user["id"], challenge_id
            )

        # Create challenge cards without adding to layout yet
        all_cards = []

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

            all_cards.append(card)

        # Arrange all cards using the new layout method
        self._rearrange_visible_cards(all_cards)

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

        # Collect visible cards
        visible_cards = []

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

            # Collect visible cards for re-layout
            if show:
                visible_cards.append(card)

        # Re-arrange visible cards to eliminate blank spaces
        self._rearrange_visible_cards(visible_cards)

    def _rearrange_visible_cards(self, visible_cards):
        """
        Rearrange visible cards in the grid layout to eliminate blank spaces.

        Args:
            visible_cards (list): List of visible challenge cards
        """
        # Remove all cards from layout first
        for card_id, card in self.challenge_cards.items():
            self.challenges_layout.removeWidget(card)

        # Calculate optimal column count
        container_width = self.challenges_widget.width()
        if container_width < 400:
            max_cols = 2
        elif container_width < 900:
            max_cols = 2
        elif container_width < 1400:
            max_cols = 3
        else:
            max_cols = 4

        # Re-add only visible cards in proper grid positions
        row, col = 0, 0
        for card in visible_cards:
            self.challenges_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Set proper stretch for the last row
        if visible_cards:
            self.challenges_layout.setRowStretch(row + 1, 1)

        # Ensure proper column stretching
        for i in range(max_cols):
            self.challenges_layout.setColumnStretch(i, 1)

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
                card.update_ui(is_subscribed=True, streak=0)
            # 发射信号，通知主窗口刷新其他界面
            self.challenge_subscription_changed.emit()
            # 弹窗时始终传递主窗口parent
            challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
            subscribe_success_msg = AnimatedMessageBox(self.window())
            subscribe_success_msg.setWindowTitle("订阅成功")
            subscribe_success_msg.setText(
                f"您已成功订阅{challenge['title']}挑战！\n记得每天完成挑战并打卡哦。"
            )
            subscribe_success_msg.setIcon(QMessageBox.Icon.Information)
            subscribe_success_msg.showNonModal()

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
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要取消订阅该挑战吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.challenge_manager.unsubscribe_from_challenge(
                self.current_user["id"], challenge_id
            )
            if success:
                # --- Update the specific challenge card ---
                if challenge_id in self.challenge_cards:
                    card = self.challenge_cards[challenge_id]
                    card.update_ui(is_subscribed=False, streak=0)
                self.challenge_subscription_changed.emit()

    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        # 使用计时器延迟执行布局调整，避免频繁调整
        self.resize_timer.start(200)  # 200毫秒后执行布局调整

    def adjust_layout(self):
        """根据容器宽度调整布局"""
        if not self.challenge_cards:
            return

        # Collect currently visible cards
        visible_cards = []
        for card_id, card in self.challenge_cards.items():
            if card.isVisible():
                visible_cards.append(card)

        # Re-arrange using the consistent method
        self._rearrange_visible_cards(visible_cards)

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
            already_checked_msg = AnimatedMessageBox(self.window())
            already_checked_msg.setWindowTitle("已打卡")
            already_checked_msg.setText(
                "您今天已经完成了这个挑战的打卡！\n明天再来继续保持吧。"
            )
            already_checked_msg.setIcon(QMessageBox.Icon.Information)
            already_checked_msg.showNonModal()
            return

        # Ask for confirmation using AnimatedMessageBox
        challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要完成该挑战吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
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
                checkin_success_msg = AnimatedMessageBox(self.window())
                checkin_success_msg.setWindowTitle("打卡成功")
                checkin_success_msg.setText(
                    f"恭喜您完成今日{challenge['title']}挑战！\n您已连续打卡 {streak} 天。"
                )
                checkin_success_msg.setIcon(QMessageBox.Icon.Information)
                checkin_success_msg.showNonModal()
