from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QCalendarWidget, QComboBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QMessageBox, # Keep QMessageBox for Icon enum
    QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot, QDate, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QTextCharFormat, QBrush

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox

import datetime


class ProgressWidget(QWidget):
    """
    Widget for displaying and managing progress.
    """

    def __init__(self, progress_tracker, challenge_manager):
        """
        Initialize the progress widget.

        Args:
            progress_tracker: Progress tracker instance
            challenge_manager: Challenge manager instance
        """
        super().__init__()

        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15) # Add spacing between main sections

        # Header layout
        self.header_layout = QHBoxLayout()

        # Title
        self.title_label = QLabel("打卡记录")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.header_layout.addWidget(self.title_label)

        # Filter layout
        self.filter_layout = QHBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignRight)

        # Challenge filter
        self.challenge_label = QLabel("挑战:")
        self.challenge_combo = QComboBox()
        self.challenge_combo.addItem("全部挑战", None)
        self.challenge_combo.currentIndexChanged.connect(self.load_progress)
        self.filter_layout.addWidget(self.challenge_label)
        self.filter_layout.addWidget(self.challenge_combo)

        # Time range filter
        self.range_label = QLabel("时间范围:")
        self.range_combo = QComboBox()
        self.range_combo.addItem("最近7天", 7)
        self.range_combo.addItem("最近30天", 30)
        self.range_combo.addItem("最近90天", 90)
        self.range_combo.addItem("全部记录", None)
        self.range_combo.currentIndexChanged.connect(self.load_progress)
        self.filter_layout.addWidget(self.range_label)
        self.filter_layout.addWidget(self.range_combo)

        self.header_layout.addLayout(self.filter_layout)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addSpacing(10) # Add spacing after header

        # Content layout (Calendar and Table)
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(15) # Add spacing between calendar and table

        # Calendar widget
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow expansion
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar_widget.setSelectionMode(QCalendarWidget.SingleSelection)
        self.calendar_widget.clicked.connect(self.calendar_date_clicked)
        self.content_layout.addWidget(self.calendar_widget, 1) # Give calendar stretch factor 1

        # Progress table
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(["日期", "挑战", "分类", "操作"])
        self.progress_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.progress_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.progress_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.progress_table.setAlternatingRowColors(True)
        self.content_layout.addWidget(self.progress_table, 2)  # Give table stretch factor 2 (more space)

        self.main_layout.addLayout(self.content_layout)
        self.main_layout.addSpacing(15) # Add spacing before bottom section

        # Bottom layout for Stats and Achievements (Changed to QVBoxLayout)
        self.bottom_layout = QVBoxLayout() # Changed from QHBoxLayout to QVBoxLayout
        self.bottom_layout.setSpacing(15) # Add spacing between stats and achievements

        # Stats GroupBox
        self.stats_group = QGroupBox("统计数据")
        self.stats_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Expand horizontally, fixed height
        self.stats_layout = QVBoxLayout(self.stats_group)  # Use QVBoxLayout for vertical stats
        self.stats_layout.setAlignment(Qt.AlignTop)

        # Total check-ins
        self.total_label = QLabel("总打卡次数: 0")
        self.stats_layout.addWidget(self.total_label)

        # Current streak
        self.streak_label = QLabel("当前连续打卡: 0 天")
        self.stats_layout.addWidget(self.streak_label)

        # Completion rate
        self.rate_label = QLabel("完成率: 0%")
        self.stats_layout.addWidget(self.rate_label)
        self.stats_layout.addStretch()  # Push stats to the top

        self.bottom_layout.addWidget(self.stats_group) # Add stats group directly

        # Achievements GroupBox
        self.achievements_group = QGroupBox("我的成就")
        self.achievements_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding) # Allow vertical expansion
        self.achievements_layout = QVBoxLayout(self.achievements_group)  # Main layout for achievements

        # Placeholder for achievements/badges display
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！") # Updated default text
        self.achievements_placeholder.setAlignment(Qt.AlignCenter)
        self.achievements_layout.addWidget(self.achievements_placeholder)  # Using placeholder for now

        self.bottom_layout.addWidget(self.achievements_group) # Add achievements group directly

        self.main_layout.addLayout(self.bottom_layout)  # Add the combined bottom layout

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information
        """
        self.current_user = user

        if user:
            # Load user's subscribed challenges
            self.load_user_challenges()

            # Load progress
            self.load_progress()
        else:
            # Clear progress
            self.clear_progress()

    def load_user_challenges(self):
        """Load user's subscribed challenges."""
        if not self.current_user:
            return

        # Get user's subscribed challenges
        challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])

        # Clear and repopulate challenge combo
        self.challenge_combo.clear()
        self.challenge_combo.addItem("全部挑战", None)

        for challenge in challenges:
            self.challenge_combo.addItem(challenge["title"], challenge["id"])

    def load_progress(self):
        """Load and display progress."""
        if not self.current_user:
            return

        # Get filter values
        challenge_id = self.challenge_combo.currentData()
        days = self.range_combo.currentData()

        # Calculate date range
        end_date = datetime.date.today()
        start_date = None
        if days:
            start_date = end_date - datetime.timedelta(days=days - 1)

        # Get check-ins
        if challenge_id:
            check_ins = self.progress_tracker.get_check_ins(
                self.current_user["id"],
                challenge_id,
                start_date.isoformat() if start_date else None,
                end_date.isoformat()
            )

            # Get challenge details
            challenge = self.challenge_manager.get_challenge_by_id(challenge_id)

            # Calculate streak
            streak = self.progress_tracker.get_streak(
                self.current_user["id"], challenge_id
            )

            # Calculate completion rate
            rate = self.progress_tracker.get_completion_rate(
                self.current_user["id"], challenge_id, days or 30
            )

            # Update stats
            self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            self.streak_label.setText(f"当前连续打卡: {streak} 天")
            self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
        else:
            check_ins = self.progress_tracker.get_all_user_check_ins(
                self.current_user["id"],
                start_date.isoformat() if start_date else None,
                end_date.isoformat()
            )

            # Calculate total unique days with check-ins
            unique_dates = set(ci["check_in_date"] for ci in check_ins)

            # Update stats
            self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            self.streak_label.setText("当前连续打卡: - 天")

            if days:
                rate = len(unique_dates) / days
                self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
            else:
                self.rate_label.setText("完成率: - %")

        # Update calendar
        self.update_calendar(check_ins)

        # Update table
        self.update_table(check_ins)

        # Load and display achievements
        self.load_achievements()

    def update_calendar(self, check_ins):
        """Update the calendar view with check-in dates."""
        # Clear previous formatting
        default_format = QTextCharFormat()  # Use QTextCharFormat
        self.calendar_widget.setDateTextFormat(QDate(), default_format)  # Clear all formats first

        # Highlight check-in dates
        check_in_format = QTextCharFormat()  # Use QTextCharFormat
        check_in_format.setBackground(QBrush(QColor("#A5D6A7")))  # Use a color from main.qss
        check_in_format.setForeground(QBrush(QColor("#212121")))  # Ensure text is readable

        # Apply format to each check-in date
        for check_in in check_ins:
            date = QDate.fromString(check_in["check_in_date"], "yyyy-MM-dd")
            if date.isValid():
                # Retrieve existing format to avoid overwriting other formats (like today's highlight)
                existing_format = self.calendar_widget.dateTextFormat(date)
                # Merge formats - background from check-in, keep existing foreground/font etc.
                existing_format.setBackground(check_in_format.background())
                self.calendar_widget.setDateTextFormat(date, existing_format)

    def update_table(self, check_ins):
        """
        Update the table with check-in records.

        Args:
            check_ins (list): List of check-in dictionaries
        """
        # Clear table
        self.progress_table.setRowCount(0)

        # Add check-ins to table
        for i, check_in in enumerate(check_ins):
            self.progress_table.insertRow(i)

            # Date
            date_str = check_in["check_in_date"]
            date_obj = datetime.date.fromisoformat(date_str)
            formatted_date = date_obj.strftime("%Y-%m-%d (%a)")
            date_item = QTableWidgetItem(formatted_date)
            self.progress_table.setItem(i, 0, date_item)

            # Challenge
            challenge_title = check_in.get("challenge_title")
            if not challenge_title:
                challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
                challenge_title = challenge["title"] if challenge else "未知挑战"
            challenge_item = QTableWidgetItem(challenge_title)
            self.progress_table.setItem(i, 1, challenge_item)

            # Category
            category = check_in.get("category")
            if not category:
                challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
                category = challenge["category"] if challenge else "未知分类"
            category_item = QTableWidgetItem(category)
            self.progress_table.setItem(i, 2, category_item)

            # Action button
            undo_button = QPushButton("撤销")
            undo_button.setObjectName("undo_button")
            undo_button.setIcon(QIcon(":/icons/rotate-ccw.svg"))
            undo_button.setIconSize(QSize(16, 16))
            undo_button.clicked.connect(lambda checked, ci=check_in: self.undo_check_in(ci))
            self.progress_table.setCellWidget(i, 3, undo_button)

    def clear_progress(self):
        """Clear progress display."""
        # Clear challenge combo
        self.challenge_combo.clear()
        self.challenge_combo.addItem("全部挑战", None)

        # Reset calendar
        self.calendar_widget.setDateTextFormat(QDate(), QTextCharFormat())

        # Clear table
        self.progress_table.setRowCount(0)

        # Reset stats
        self.total_label.setText("总打卡次数: 0")
        self.streak_label.setText("当前连续打卡: 0 天")
        self.rate_label.setText("完成率: 0%")

        # Clear achievements display
        self.clear_achievements()

    def calendar_date_clicked(self, date):
        """
        Handle calendar date click.

        Args:
            date (QDate): Clicked date
        """
        if not self.current_user:
            return

        # Convert QDate to ISO format
        date_str = f"{date.year()}-{date.month():02d}-{date.day():02d}"

        # Get challenge ID
        challenge_id = self.challenge_combo.currentData()

        # Get check-ins for the selected date
        if challenge_id:
            check_ins = self.progress_tracker.get_check_ins(
                self.current_user["id"],
                challenge_id,
                date_str,
                date_str
            )
        else:
            check_ins = self.progress_tracker.get_all_user_check_ins(
                self.current_user["id"],
                date_str,
                date_str
            )

        # Update table to show only the selected date
        self.update_table(check_ins)

    def undo_check_in(self, check_in):
        """
        Undo a check-in.

        Args:
            check_in (dict): Check-in information
        """
        if not self.current_user:
            return

        # Ask for confirmation using AnimatedMessageBox
        challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
        challenge_title = challenge["title"] if challenge else "未知挑战"

        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
            self,
            "撤销打卡",
            f"确定要撤销 {check_in['check_in_date']} 的 {challenge_title} 打卡记录吗？\n"
            f"这可能会影响您的连续打卡天数。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.progress_tracker.undo_check_in(
                self.current_user["id"],
                check_in["challenge_id"],
                check_in["check_in_date"]
            )

            if success:
                # Reload progress
                self.load_progress()

    def load_achievements(self):
        """Load and display user achievements/badges."""
        if not self.current_user:
            return

        # TODO: Get achievements from progress_tracker
        # achievements = self.progress_tracker.get_achievements(self.current_user["id"])
        achievements = []  # Placeholder

        if achievements:
            self.achievements_placeholder.hide()
            pass  # Replace with actual implementation
        else:
            self.achievements_placeholder.setText("暂无成就，继续努力吧！")
            self.achievements_placeholder.show()

    def clear_achievements(self):
        """Clear the achievements display area."""
        self.achievements_placeholder.setText("成就徽章将在此处展示。")
        self.achievements_placeholder.show()
