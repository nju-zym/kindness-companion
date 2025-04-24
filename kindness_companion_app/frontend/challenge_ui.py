from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QMessageBox, QGridLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
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

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        self.title_label = QLabel(self.challenge["title"])
        self.title_label.setObjectName("title_label")  # Use object name if specific styling needed
        self.main_layout.addWidget(self.title_label)

        # Description
        self.description_label = QLabel(self.challenge["description"])
        self.description_label.setWordWrap(True)
        self.main_layout.addWidget(self.description_label)

        # Metadata layout
        self.meta_layout = QHBoxLayout()

        # Category
        self.category_label = QLabel(f"分类: {self.challenge['category']}")
        self.meta_layout.addWidget(self.category_label)

        # Difficulty
        difficulty_text = "★" * self.challenge["difficulty"]
        self.difficulty_label = QLabel(f"难度: {difficulty_text}")
        self.meta_layout.addWidget(self.difficulty_label)

        # Streak (if subscribed)
        if self.is_subscribed and self.streak > 0:
            self.streak_label = QLabel(f"连续打卡: {self.streak}天")
            self.streak_label.setObjectName("streak_label")  # Add object name if needed
            self.meta_layout.addWidget(self.streak_label)

        self.main_layout.addLayout(self.meta_layout)

        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignRight)

        icon_size = QSize(16, 16)  # Icon size for card buttons

        # Subscribe/Unsubscribe button
        if self.is_subscribed:
            self.subscribe_button = QPushButton("取消订阅")
            self.subscribe_button.setObjectName("unsubscribe_button")  # Set object name
            self.subscribe_button.setIcon(QIcon(":/icons/x-circle.svg"))  # Add icon
            self.subscribe_button.setIconSize(icon_size)
            self.subscribe_button.clicked.connect(
                lambda: self.unsubscribe_clicked.emit(self.challenge["id"])
            )

            # Check-in button
            self.check_in_button = QPushButton("今日打卡")
            self.check_in_button.setObjectName("check_in_button")  # Set object name
            self.check_in_button.setIcon(QIcon(":/icons/check-square.svg"))  # Add icon
            self.check_in_button.setIconSize(icon_size)
            self.check_in_button.clicked.connect(
                lambda: self.check_in_clicked.emit(self.challenge["id"])
            )
            self.button_layout.addWidget(self.check_in_button)
        else:
            self.subscribe_button = QPushButton("订阅挑战")
            self.subscribe_button.setObjectName("subscribe_button")  # Set object name
            self.subscribe_button.setIcon(QIcon(":/icons/plus-circle.svg"))  # Add icon
            self.subscribe_button.setIconSize(icon_size)
            self.subscribe_button.clicked.connect(
                lambda: self.subscribe_clicked.emit(self.challenge["id"])
            )

        self.button_layout.addWidget(self.subscribe_button)

        self.main_layout.addLayout(self.button_layout)

    def update_subscription(self, is_subscribed, streak=0):
        """
        Update the subscription status.

        Args:
            is_subscribed (bool): Whether the user is subscribed
            streak (int): Current streak
        """
        # Store new values
        self.is_subscribed = is_subscribed
        self.streak = streak

        # Clear layout
        self.deleteLater()


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

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header layout
        self.header_layout = QHBoxLayout()

        # Title
        self.title_label = QLabel("善行挑战列表")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.header_layout.addWidget(self.title_label)

        # Filter layout
        self.filter_layout = QHBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignRight)

        # Category filter
        self.category_label = QLabel("分类:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类", None)
        self.category_combo.currentIndexChanged.connect(self.filter_challenges)
        self.filter_layout.addWidget(self.category_label)
        self.filter_layout.addWidget(self.category_combo)

        # Difficulty filter
        self.difficulty_label = QLabel("难度:")
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItem("全部难度", None)
        for i in range(1, 6):
            self.difficulty_combo.addItem("★" * i, i)
        self.difficulty_combo.currentIndexChanged.connect(self.filter_challenges)
        self.filter_layout.addWidget(self.difficulty_label)
        self.filter_layout.addWidget(self.difficulty_combo)

        # Subscription filter
        self.subscription_label = QLabel("订阅:")
        self.subscription_combo = QComboBox()
        self.subscription_combo.addItem("全部挑战", None)
        self.subscription_combo.addItem("已订阅", True)
        self.subscription_combo.addItem("未订阅", False)
        self.subscription_combo.currentIndexChanged.connect(self.filter_challenges)
        self.filter_layout.addWidget(self.subscription_label)
        self.filter_layout.addWidget(self.subscription_combo)

        self.header_layout.addLayout(self.filter_layout)

        self.main_layout.addLayout(self.header_layout)

        # Scroll area for challenges
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # Container widget for challenges
        self.challenges_widget = QWidget()
        self.challenges_layout = QGridLayout(self.challenges_widget)
        self.challenges_layout.setContentsMargins(0, 0, 0, 0)
        self.challenges_layout.setSpacing(15)

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
        max_cols = 2  # Number of columns in the grid

        for challenge in challenges:
            is_subscribed = challenge["id"] in subscribed_ids
            streak = streaks.get(challenge["id"], 0) if is_subscribed else 0

            card = ChallengeCard(challenge, is_subscribed, streak)
            card.subscribe_clicked.connect(self.subscribe_to_challenge)
            card.unsubscribe_clicked.connect(self.unsubscribe_from_challenge)
            card.check_in_clicked.connect(self.check_in_challenge)

            self.challenges_layout.addWidget(card, row, col)
            self.challenge_cards[challenge["id"]] = card

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

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
            # Update the challenge card
            self.load_challenges()  # Reload all challenges for simplicity

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
                # Update the challenge card
                self.load_challenges()  # Reload all challenges for simplicity

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

                # Show success message non-modally using AnimatedMessageBox
                checkin_success_msg = AnimatedMessageBox(self) # Use AnimatedMessageBox
                checkin_success_msg.setWindowTitle("打卡成功")
                checkin_success_msg.setText(f"恭喜您完成今日{challenge['title']}挑战！\n您已连续打卡 {streak} 天。")
                checkin_success_msg.setIcon(QMessageBox.Information)
                checkin_success_msg.showNonModal() # Use custom non-modal method

                # Update the challenge card
                self.load_challenges()  # Reload all challenges for simplicity
