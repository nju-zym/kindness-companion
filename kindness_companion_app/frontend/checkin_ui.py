from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QGridLayout,
    QCalendarWidget,
    QSizePolicy,
    QScrollArea,
)
from PySide6.QtCore import Qt, Slot, QSize, QDate, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QPalette
import datetime
import random

# Import AnimatedMessageBox
from .widgets.animated_message_box import AnimatedMessageBox


class StreakCalendar(QWidget):
    """
    Widget for displaying a calendar with check-in streaks highlighted.
    """

    def __init__(self, progress_tracker, user_id=None, challenge_id=None):
        super().__init__()
        self.progress_tracker = progress_tracker
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.check_in_dates = []

        self.setup_ui()

    def setup_ui(self):
        """Set up the calendar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        self.title_label = QLabel("打卡日历")
        self.title_label.setObjectName("calendar_title_label")
        layout.addWidget(self.title_label)

        # Calendar grid (simplified version without using QCalendarWidget)
        self.calendar_frame = QFrame()
        self.calendar_frame.setObjectName("calendar_frame")
        self.calendar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        self.calendar_layout = QGridLayout(self.calendar_frame)
        self.calendar_layout.setSpacing(2)

        # Add day headers
        days = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setObjectName("calendar_header")
            self.calendar_layout.addWidget(label, 0, i)

        # Create day cells (5 weeks x 7 days)
        self.day_cells = []
        for row in range(1, 6):
            row_cells = []
            for col in range(7):
                cell = QLabel()
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setObjectName("calendar_day")
                cell.setFixedSize(30, 30)
                self.calendar_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.day_cells.append(row_cells)

        layout.addWidget(self.calendar_frame)

        # Legend
        legend_layout = QHBoxLayout()

        # Check-in day
        checkin_indicator = QLabel()
        checkin_indicator.setObjectName("calendar_checkin_indicator")
        checkin_indicator.setFixedSize(15, 15)
        legend_layout.addWidget(checkin_indicator)
        legend_layout.addWidget(QLabel("已打卡"))

        legend_layout.addStretch()

        # Today
        today_indicator = QLabel()
        today_indicator.setObjectName("calendar_today_indicator")
        today_indicator.setFixedSize(15, 15)
        legend_layout.addWidget(today_indicator)
        legend_layout.addWidget(QLabel("今天"))

        layout.addLayout(legend_layout)

    def update_calendar(self, user_id=None, challenge_id=None):
        """Update the calendar with check-in data."""
        if user_id:
            self.user_id = user_id
        if challenge_id:
            self.challenge_id = challenge_id

        if not self.user_id or not self.challenge_id:
            return

        # Get current month
        today = datetime.date.today()
        start_of_month = datetime.date(today.year, today.month, 1)

        # Calculate days in month and first day of month (0 = Monday, 6 = Sunday)
        if today.month == 12:
            next_month = datetime.date(today.year + 1, 1, 1)
        else:
            next_month = datetime.date(today.year, today.month + 1, 1)
        days_in_month = (next_month - datetime.timedelta(days=1)).day
        first_weekday = start_of_month.weekday()  # 0 = Monday

        # Get check-in data for this month
        month_start = start_of_month.isoformat()
        month_end = (next_month - datetime.timedelta(days=1)).isoformat()

        check_ins = self.progress_tracker.get_check_ins(
            self.user_id, self.challenge_id, month_start, month_end
        )
        self.check_in_dates = [
            datetime.date.fromisoformat(ci["check_in_date"]).day for ci in check_ins
        ]

        # Update calendar cells
        for row in range(5):
            for col in range(7):
                cell = self.day_cells[row][col]
                day_num = row * 7 + col + 1 - first_weekday

                if 1 <= day_num <= days_in_month:
                    cell.setText(str(day_num))

                    # Style for check-in days
                    if day_num in self.check_in_dates:
                        cell.setObjectName("calendar_day_checkin")
                    # Style for today
                    elif day_num == today.day:
                        cell.setObjectName("calendar_day_today")
                    else:
                        cell.setObjectName("calendar_day")

                    # Apply styles
                    cell.setStyleSheet("")  # Reset style
                    cell.style().unpolish(cell)
                    cell.style().polish(cell)
                else:
                    cell.setText("")
                    cell.setObjectName("calendar_day_inactive")
                    cell.setStyleSheet("")
                    cell.style().unpolish(cell)
                    cell.style().polish(cell)


class MotivationalQuotes:
    """Class to provide motivational quotes about kindness."""

    quotes = [
        "善良是人类最伟大的美德。 —— 孔子",
        "善良是一种语言，聋子能听见，盲人能看见。 —— 马克·吐温",
        "善良是世界上最强大的力量。 —— 佚名",
        "一个人的善良，足以改变一个人的世界。 —— 佚名",
        "善良是一种选择，每天都可以重新选择。 —— 佚名",
        "善良不是软弱，而是内心的强大。 —— 佚名",
        "善良是一种习惯，需要每天练习。 —— 佚名",
        "善良的行为，无论多小，都不会白费。 —— 伊索",
        "善良是人类心灵最美的花朵。 —— 佚名",
        "善良是照亮他人同时也照亮自己的灯。 —— 佚名",
        "善良不求回报，但总会以某种方式回到你身边。 —— 佚名",
        "善良是最简单却最有力量的行为。 —— 佚名",
        "善良是心灵的阳光。 —— 佚名",
        "善良是一种能量，它能传递并感染他人。 —— 佚名",
        "善良不是一时的情绪，而是持久的品格。 —— 佚名",
    ]

    @staticmethod
    def get_random_quote():
        """Return a random motivational quote."""
        return random.choice(MotivationalQuotes.quotes)


class ChallengeDetailPanel(QFrame):
    """
    Widget for displaying detailed information about a challenge.
    """

    def __init__(self, challenge=None):
        super().__init__()
        self.challenge = challenge
        self.setObjectName("challenge_detail_panel")
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI for challenge details."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Challenge title
        self.title_label = QLabel()
        self.title_label.setObjectName("challenge_detail_title")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("detail_separator")
        layout.addWidget(separator)

        # Challenge metadata
        metadata_layout = QHBoxLayout()

        # Category
        self.category_layout = QHBoxLayout()
        self.category_label = QLabel("分类:")
        self.category_value = QLabel()
        self.category_layout.addWidget(self.category_label)
        self.category_layout.addWidget(self.category_value)
        metadata_layout.addLayout(self.category_layout)

        metadata_layout.addStretch()

        # Difficulty
        self.difficulty_layout = QHBoxLayout()
        self.difficulty_label = QLabel("难度:")
        self.difficulty_value = QLabel()
        self.difficulty_layout.addWidget(self.difficulty_label)
        self.difficulty_layout.addWidget(self.difficulty_value)
        metadata_layout.addLayout(self.difficulty_layout)

        layout.addLayout(metadata_layout)

        # Description
        self.description_label = QLabel("描述:")
        layout.addWidget(self.description_label)

        self.description_value = QLabel()
        self.description_value.setObjectName("challenge_detail_description")
        self.description_value.setWordWrap(True)
        layout.addWidget(self.description_value)

        # Why This Matters section
        self.impact_label = QLabel("为什么这很重要:")
        layout.addWidget(self.impact_label)

        self.impact_value = QLabel()
        self.impact_value.setObjectName("challenge_detail_impact")
        self.impact_value.setWordWrap(True)
        layout.addWidget(self.impact_value)

        # Motivational quote
        self.quote_label = QLabel()
        self.quote_label.setObjectName("motivational_quote")
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.quote_label)

        layout.addStretch()

        # Update with empty challenge initially
        self.update_challenge(self.challenge)

    def update_challenge(self, challenge):
        """Update the panel with challenge details."""
        self.challenge = challenge

        if not challenge:
            self.title_label.setText("请选择一个挑战")
            self.category_value.setText("")
            self.difficulty_value.setText("")
            self.description_value.setText("")
            self.impact_value.setText("")
            self.quote_label.setText("")
            return

        # Update UI elements with challenge data
        self.title_label.setText(challenge["title"])
        self.category_value.setText(challenge["category"])

        # Display difficulty as stars
        difficulty_stars = "★" * challenge["difficulty"] + "☆" * (
            5 - challenge["difficulty"]
        )
        self.difficulty_value.setText(difficulty_stars)

        self.description_value.setText(challenge["description"])

        # Generate impact text based on challenge category
        impact_texts = {
            "日常行为": "日常的小善举能够创造积极的连锁反应，让世界变得更美好。每一个微笑、每一句鼓励的话语都能照亮他人的一天。",
            "社区服务": "通过帮助社区中的他人，你不仅改善了他们的生活，也增强了社区的凝聚力和互助精神。",
            "环保": "环保行动对地球的健康至关重要。每个人的小行动累积起来，能够产生巨大的积极影响。",
            "精神成长": "内心的成长和自我提升能够帮助你成为更好的自己，也能够更好地帮助他人。",
            "自我提升": "自我提升不仅仅是为了自己，也是为了能够更好地服务他人和社会。",
            "人际关系": "健康的人际关系是幸福生活的基础。通过善待他人，你也在创造一个更和谐的社交环境。",
        }

        category = challenge["category"]
        self.impact_value.setText(
            impact_texts.get(
                category, "这个挑战能够帮助你培养善良的品质，对自己和他人都有积极影响。"
            )
        )

        # Set a random motivational quote
        self.quote_label.setText(MotivationalQuotes.get_random_quote())


class CheckinWidget(QWidget):
    """
    Widget for daily check-in and reflection.
    """

    # Signal to notify when a check-in is successful
    check_in_successful = Signal(int)  # Challenge ID

    def __init__(self, progress_tracker, challenge_manager):
        """
        Initialize the check-in widget.

        Args:
            progress_tracker: Progress tracker instance.
            challenge_manager: Challenge manager instance.
        """
        super().__init__()
        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user = None
        self.current_challenge = None
        self.quote_timer = QTimer(self)
        self.quote_timer.timeout.connect(self.update_quote)
        self.quote_timer.start(30000)  # Update quote every 30 seconds

        self.setup_ui()

    def update_quote(self):
        """Update the motivational quote in the challenge detail panel."""
        if hasattr(self, "challenge_detail_panel"):
            if self.challenge_detail_panel.challenge:
                self.challenge_detail_panel.quote_label.setText(
                    MotivationalQuotes.get_random_quote()
                )

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(18)

        # Page title
        self.title_label = QLabel("📅 每日打卡与反思")
        self.title_label.setObjectName("title_label")
        main_layout.addWidget(self.title_label)

        # Main content layout (horizontal split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left panel (challenge list and check-in form)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # Challenge Selection Label
        self.challenge_label = QLabel("选择要打卡的挑战:")
        self.challenge_label.setObjectName("section_label")
        left_layout.addWidget(self.challenge_label)

        # Challenge List
        self.challenge_list = QListWidget()
        self.challenge_list.setMinimumHeight(120)
        self.challenge_list.setObjectName("challenge_list")
        self.challenge_list.currentItemChanged.connect(self.on_challenge_selected)
        left_layout.addWidget(self.challenge_list)

        # Current streak display
        self.streak_container = QFrame()
        self.streak_container.setObjectName("streak_container")
        streak_layout = QHBoxLayout(self.streak_container)

        self.streak_icon = QLabel("🔥")
        self.streak_icon.setObjectName("streak_icon")
        streak_layout.addWidget(self.streak_icon)

        self.streak_label = QLabel("当前连续打卡: 0 天")
        self.streak_label.setObjectName("streak_label")
        streak_layout.addWidget(self.streak_label)

        streak_layout.addStretch()
        left_layout.addWidget(self.streak_container)

        # Reflection Notes Label
        self.notes_label = QLabel("今日感想:")
        self.notes_label.setObjectName("section_label")
        left_layout.addWidget(self.notes_label)

        # Reflection Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("记录一下今天的感想吧...(可选)")
        self.notes_edit.setMinimumHeight(100)
        left_layout.addWidget(self.notes_edit)

        # Check-in Button
        self.checkin_button = QPushButton(" 确认打卡")
        self.checkin_button.setObjectName("checkin_button")
        self.checkin_button.setMinimumHeight(28)
        checkin_icon = QIcon(":/icons/check-circle.svg")
        if not checkin_icon.isNull():
            self.checkin_button.setIcon(checkin_icon)
            self.checkin_button.setIconSize(QSize(20, 20))
        self.checkin_button.clicked.connect(self.submit_checkin)
        left_layout.addWidget(
            self.checkin_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        # Add left panel to content layout
        content_layout.addWidget(left_panel, 1)  # 1 = stretch factor

        # Right panel (challenge details and calendar)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Challenge details panel
        self.challenge_detail_panel = ChallengeDetailPanel()
        self.challenge_detail_panel.setMinimumHeight(300)
        right_layout.addWidget(self.challenge_detail_panel)

        # Calendar for tracking check-ins
        self.calendar = StreakCalendar(self.progress_tracker)
        right_layout.addWidget(self.calendar)

        # Add right panel to content layout
        content_layout.addWidget(right_panel, 1)  # 1 = stretch factor

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        # Initially disable form until user is set and challenges loaded
        self.challenge_list.setEnabled(False)
        self.notes_edit.setEnabled(False)
        self.checkin_button.setEnabled(False)
        self.streak_container.setVisible(False)

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information or None if logged out.
        """
        self.current_user = user
        if user:
            # Load challenges eligible for check-in today
            self.load_checkable_challenges()
            self.notes_edit.setEnabled(True)
        else:
            # Clear UI elements and disable
            self.challenge_list.clear()
            # Add a placeholder item when logged out
            placeholder_item = QListWidgetItem("请先登录")
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.challenge_list.addItem(placeholder_item)
            self.challenge_list.setEnabled(False)

            # Reset other UI elements
            self.notes_edit.clear()
            self.notes_edit.setEnabled(False)
            self.checkin_button.setEnabled(False)
            self.streak_container.setVisible(False)
            self.challenge_detail_panel.update_challenge(None)
            self.calendar.update_calendar(None, None)

    @Slot(QListWidgetItem, QListWidgetItem)
    def on_challenge_selected(self, current, previous):
        """Handle challenge selection change."""
        if not current or current.flags() == Qt.ItemFlag.NoItemFlags:
            self.challenge_detail_panel.update_challenge(None)
            self.streak_container.setVisible(False)
            self.calendar.update_calendar(None, None)
            return

        challenge_id = current.data(Qt.ItemDataRole.UserRole)
        if not challenge_id:
            return

        # Get full challenge data
        challenge = self.challenge_manager.get_challenge_by_id(challenge_id)
        if not challenge:
            return

        # Update challenge details panel
        self.challenge_detail_panel.update_challenge(challenge)

        # Update streak display
        if self.current_user:
            try:
                current_streak = self.progress_tracker.get_streak(
                    self.current_user["id"], challenge_id
                )
                self.streak_label.setText(f"当前连续打卡: {current_streak} 天")
                self.streak_container.setVisible(True)
            except Exception as e:
                print(f"Error getting streak: {e}")
                self.streak_container.setVisible(False)

            # Update calendar
            self.calendar.update_calendar(self.current_user["id"], challenge_id)

    def load_checkable_challenges(self):
        """Load challenges that the user is subscribed to and can check in for today into the QListWidget."""
        if not self.current_user:
            self.challenge_list.setEnabled(False)
            self.checkin_button.setEnabled(False)
            self.streak_container.setVisible(False)
            return

        self.challenge_list.clear()
        self.challenge_list.setEnabled(False)
        self.checkin_button.setEnabled(False)
        self.streak_container.setVisible(False)

        # Add a temporary loading item
        loading_item = QListWidgetItem("加载挑战中...")
        loading_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.challenge_list.addItem(loading_item)

        subscribed_challenges = self.challenge_manager.get_user_challenges(
            self.current_user["id"]
        )
        today = datetime.date.today().isoformat()
        checkable_challenges = []

        for challenge in subscribed_challenges:
            check_ins_today = self.progress_tracker.get_check_ins(
                self.current_user["id"], challenge["id"], today, today
            )
            if not check_ins_today:
                checkable_challenges.append(challenge)

        self.challenge_list.clear()

        if checkable_challenges:
            self.challenge_list.setEnabled(True)
            self.checkin_button.setEnabled(True)
            for challenge in checkable_challenges:
                item = QListWidgetItem(challenge["title"])
                item.setData(Qt.ItemDataRole.UserRole, challenge["id"])
                self.challenge_list.addItem(item)

            # Select the first item by default
            if self.challenge_list.count() > 0:
                self.challenge_list.setCurrentRow(0)
                # The on_challenge_selected slot will be called automatically
        else:
            placeholder_item = QListWidgetItem("今日已全部打卡或未订阅挑战")
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.challenge_list.addItem(placeholder_item)
            self.challenge_list.setEnabled(False)
            self.checkin_button.setEnabled(False)
            self.challenge_detail_panel.update_challenge(None)

    @Slot()
    def submit_checkin(self):
        """Handle the check-in submission."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self.window(), "错误", "用户未登录")
            return

        # Get selected item from QListWidget
        selected_item = self.challenge_list.currentItem()
        notes = self.notes_edit.toPlainText().strip()

        if selected_item is None or selected_item.flags() == Qt.ItemFlag.NoItemFlags:
            AnimatedMessageBox.showWarning(
                self.window(), "打卡失败", "请选择一个要打卡的挑战"
            )
            return

        challenge_id = selected_item.data(Qt.ItemDataRole.UserRole)
        challenge_title = selected_item.text()

        if challenge_id is None:
            AnimatedMessageBox.showWarning(
                self.window(), "打卡失败", "无法获取所选挑战的信息"
            )
            return

        # Perform check-in using progress_tracker
        success = self.progress_tracker.check_in(
            self.current_user["id"], challenge_id, notes=notes if notes else None
        )

        if success:
            # Get current streak
            try:
                current_streak = self.progress_tracker.get_streak(
                    self.current_user["id"], challenge_id
                )
                streak_message = f"\n\n🔥 当前连续打卡: {current_streak} 天！"

                # Update streak display
                self.streak_label.setText(f"当前连续打卡: {current_streak} 天")
                self.streak_container.setVisible(True)

                # Update calendar
                self.calendar.update_calendar(self.current_user["id"], challenge_id)
            except Exception as e:
                print(f"Error getting streak: {e}")
                streak_message = ""

            # Show success message
            AnimatedMessageBox.showInformation(
                self.window(),
                "打卡成功!",
                f"已成功为 '{challenge_title}' 打卡！{streak_message}",
            )

            # Clear notes and reload challenges
            self.notes_edit.clear()
            self.load_checkable_challenges()

            # Emit signal for other components that might need to update
            self.check_in_successful.emit(challenge_id)
        else:
            # This might happen if there's a race condition or DB error
            AnimatedMessageBox.showWarning(
                self.window(), "打卡失败", "无法完成打卡，请稍后重试或检查是否已打卡。"
            )
            # Reload to ensure consistency
            self.load_checkable_challenges()
