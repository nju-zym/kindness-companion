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
        """Set up the user interface with a left panel and right panel layout.""" # Removed invalid character
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header layout (Title and Filters)
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("打卡记录")
        self.title_label.setObjectName("title_label")
        self.header_layout.addWidget(self.title_label)

        self.filter_layout = QHBoxLayout()
        self.filter_layout.setAlignment(Qt.AlignRight)
        self.challenge_label = QLabel("挑战:")
        self.challenge_combo = QComboBox()
        self.challenge_combo.addItem("全部挑战", None)
        self.challenge_combo.currentIndexChanged.connect(self.load_progress)
        self.filter_layout.addWidget(self.challenge_label)
        self.filter_layout.addWidget(self.challenge_combo)
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

        # Main Content Layout (Left Panel + Right Panel)
        self.main_content_layout = QHBoxLayout()
        self.main_content_layout.setSpacing(15)

        # --- Left Panel ---
        self.left_panel_widget = QWidget()
        self.left_panel_widget.setObjectName("left_panel") # For potential styling
        self.left_panel_layout = QVBoxLayout(self.left_panel_widget)
        self.left_panel_layout.setContentsMargins(0, 0, 0, 0) # No margins for the panel itself
        self.left_panel_layout.setSpacing(15)
        self.left_panel_widget.setMaximumWidth(350) # Limit width of left panel

        # Calendar widget
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar_widget.setSelectionMode(QCalendarWidget.SingleSelection)
        self.calendar_widget.clicked.connect(self.calendar_date_clicked)
        self.left_panel_layout.addWidget(self.calendar_widget)

        # Stats GroupBox
        self.stats_group = QGroupBox("统计数据")
        self.stats_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.stats_layout = QVBoxLayout(self.stats_group)
        self.stats_layout.setAlignment(Qt.AlignTop)
        self.total_label = QLabel("总打卡次数: 0")
        self.stats_layout.addWidget(self.total_label)
        self.streak_label = QLabel("当前连续打卡: 0 天")
        self.stats_layout.addWidget(self.streak_label)
        self.rate_label = QLabel("完成率: 0%")
        self.stats_layout.addWidget(self.rate_label)
        self.stats_layout.addStretch()
        self.left_panel_layout.addWidget(self.stats_group)

        # Achievements GroupBox
        self.achievements_group = QGroupBox("我的成就")
        self.achievements_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.achievements_layout = QVBoxLayout(self.achievements_group)
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setAlignment(Qt.AlignCenter)
        self.achievements_layout.addWidget(self.achievements_placeholder)
        self.left_panel_layout.addWidget(self.achievements_group)

        # Add Left Panel to Main Content Layout
        self.main_content_layout.addWidget(self.left_panel_widget, 1) # Stretch factor 1

        # --- Right Panel (Table) ---
        # No need for an extra container widget, add table directly to the layout
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(["日期", "挑战", "分类", "操作"])
        header = self.progress_table.horizontalHeader()
        # Adjust resize modes for better column sizing
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Date
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Challenge
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Action
        self.progress_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.progress_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.progress_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.progress_table.setAlternatingRowColors(True)
        self.progress_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add Table directly to Main Content Layout
        self.main_content_layout.addWidget(self.progress_table, 3) # Stretch factor 3

        # Add Main Content Layout to Main Layout
        self.main_layout.addLayout(self.main_content_layout)

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information
        """
        self.current_user = user

        if user:
            self.load_user_challenges()
            self.load_progress()
        else:
            self.clear_progress()

    def load_user_challenges(self):
        """Load user's subscribed challenges."""
        if not self.current_user:
            return

        challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])

        self.challenge_combo.clear()
        self.challenge_combo.addItem("全部挑战", None)

        for challenge in challenges:
            self.challenge_combo.addItem(challenge["title"], challenge["id"])

    def load_progress(self):
        """Load and display progress."""
        if not self.current_user:
            return

        challenge_id = self.challenge_combo.currentData()
        days = self.range_combo.currentData()

        end_date = datetime.date.today()
        start_date = None
        if days:
            start_date = end_date - datetime.timedelta(days=days - 1)

        if challenge_id:
            check_ins = self.progress_tracker.get_check_ins(
                self.current_user["id"],
                challenge_id,
                start_date.isoformat() if start_date else None,
                end_date.isoformat()
            )
            streak = self.progress_tracker.get_streak(
                self.current_user["id"], challenge_id
            )
            rate = self.progress_tracker.get_completion_rate(
                self.current_user["id"], challenge_id, days or 30 # Default to 30 days for rate if 'All' selected
            )
            self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            self.streak_label.setText(f"当前连续打卡: {streak} 天")
            self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
        else:
            check_ins = self.progress_tracker.get_all_user_check_ins(
                self.current_user["id"],
                start_date.isoformat() if start_date else None,
                end_date.isoformat()
            )
            unique_dates = set(ci["check_in_date"] for ci in check_ins)
            self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            self.streak_label.setText("当前连续打卡: - 天") # Streak is challenge-specific
            if days:
                # Calculate rate based on unique days checked in within the period
                rate = len(unique_dates) / days if days > 0 else 0
                self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
            else:
                self.rate_label.setText("完成率: - %") # Rate doesn't make sense for 'All'

        self.update_calendar(check_ins)
        self.update_table(check_ins)
        self.load_achievements()

    def update_calendar(self, check_ins):
        """Update the calendar view with check-in dates."""
        # Clear previous formatting by setting a default format for a null date
        default_format = QTextCharFormat()
        self.calendar_widget.setDateTextFormat(QDate(), default_format)

        # Highlight check-in dates
        check_in_format = QTextCharFormat()
        check_in_format.setBackground(QBrush(QColor("#A5D6A7"))) # Use a theme-friendly color
        check_in_format.setForeground(QBrush(QColor("#212121"))) # Ensure text is readable

        check_in_dates = {QDate.fromString(ci["check_in_date"], "yyyy-MM-dd") for ci in check_ins}

        # Iterate through visible month to apply/clear formats efficiently
        current_month = self.calendar_widget.monthShown()
        current_year = self.calendar_widget.yearShown()
        start_date = QDate(current_year, current_month, 1)
        end_date = start_date.addMonths(1).addDays(-1)

        date_iter = start_date
        while date_iter <= end_date:
            existing_format = self.calendar_widget.dateTextFormat(date_iter)
            if date_iter in check_in_dates:
                # Apply check-in background, keep other properties
                existing_format.setBackground(check_in_format.background())
                existing_format.setForeground(check_in_format.foreground())
            else:
                # Explicitly remove check-in background if date is not in check_ins
                # Check if the current background is the check-in color before resetting
                if existing_format.background() == check_in_format.background():
                     existing_format.setBackground(default_format.background())
                     # Reset foreground only if it was set by check-in format
                     if existing_format.foreground() == check_in_format.foreground():
                         existing_format.setForeground(default_format.foreground())

            self.calendar_widget.setDateTextFormat(date_iter, existing_format)
            date_iter = date_iter.addDays(1)


    def update_table(self, check_ins):
        """
        Update the table with check-in records.

        Args:
            check_ins (list): List of check-in dictionaries
        """
        self.progress_table.setRowCount(0)

        # Sort check-ins by date descending
        sorted_check_ins = sorted(check_ins, key=lambda x: x['check_in_date'], reverse=True)

        for i, check_in in enumerate(sorted_check_ins):
            self.progress_table.insertRow(i)

            date_str = check_in["check_in_date"]
            try:
                date_obj = datetime.date.fromisoformat(date_str)
                formatted_date = date_obj.strftime("%Y-%m-%d (%a)")
            except ValueError:
                formatted_date = date_str # Fallback if format is wrong
            date_item = QTableWidgetItem(formatted_date)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.progress_table.setItem(i, 0, date_item)

            challenge_title = check_in.get("challenge_title")
            if not challenge_title:
                challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
                challenge_title = challenge["title"] if challenge else "未知挑战"
            challenge_item = QTableWidgetItem(challenge_title)
            self.progress_table.setItem(i, 1, challenge_item)

            category = check_in.get("category")
            if not category:
                challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
                category = challenge["category"] if challenge else "未知分类"
            category_item = QTableWidgetItem(category)
            category_item.setTextAlignment(Qt.AlignCenter)
            self.progress_table.setItem(i, 2, category_item)

            # Action button (Undo)
            button_widget = QWidget() # Use a container widget for centering
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2) # Small margins
            button_layout.setAlignment(Qt.AlignCenter)
            undo_button = QPushButton("撤销")
            undo_button.setObjectName("undo_button")
            undo_button.setIcon(QIcon(":/icons/rotate-ccw.svg"))
            undo_button.setIconSize(QSize(16, 16))
            undo_button.setFixedSize(QSize(80, 28)) # Fixed size for consistency
            undo_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            undo_button.clicked.connect(lambda checked=False, ci=check_in: self.undo_check_in(ci))
            button_layout.addWidget(undo_button)
            self.progress_table.setCellWidget(i, 3, button_widget)

        # Adjust row heights after populating
        self.progress_table.resizeRowsToContents()

    def clear_progress(self):
        """Clear progress display."""
        self.challenge_combo.clear()
        self.challenge_combo.addItem("全部挑战", None)

        # Reset calendar formatting
        self.update_calendar([]) # Update with empty list to clear highlights

        self.progress_table.setRowCount(0)

        self.total_label.setText("总打卡次数: 0")
        self.streak_label.setText("当前连续打卡: 0 天")
        self.rate_label.setText("完成率: 0%")

        self.clear_achievements()

    def calendar_date_clicked(self, date):
        """
        Handle calendar date click: Filter table to show only selected date.
        Does not change the overall filters (Challenge/Range).
        Args:
            date (QDate): Clicked date
        """
        if not self.current_user:
            return

        date_str = date.toString("yyyy-MM-dd")
        challenge_id = self.challenge_combo.currentData()

        # Get check-ins specifically for the clicked date
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

        # Update table only
        self.update_table(check_ins)
        # Do NOT call load_progress() here, as it would reset the date filter

    def undo_check_in(self, check_in):
        """
        Undo a check-in after confirmation.

        Args:
            check_in (dict): Check-in information
        """
        if not self.current_user:
            return

        challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
        challenge_title = challenge["title"] if challenge else "未知挑战"

        reply = AnimatedMessageBox.showQuestion(
            self,
            "撤销打卡",
            f"确定要撤销 {check_in['check_in_date']} 的 {challenge_title} 打卡记录吗？\n"
            f"这可能会影响您的连续打卡天数和成就。",
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
                AnimatedMessageBox.showInformation(self, "操作成功", "打卡记录已撤销。")
                # Reload progress to reflect the change everywhere
                self.load_progress()
            else:
                 AnimatedMessageBox.showWarning(self, "操作失败", "无法撤销打卡记录，请稍后再试。")

    def load_achievements(self):
        """Load and display user achievements/badges."""
        if not self.current_user:
            return

        # TODO: Implement achievement fetching and display logic
        # achievements = self.progress_tracker.get_achievements(self.current_user["id"])
        achievements = []  # Placeholder

        # Clear previous achievements (if any)
        while self.achievements_layout.count() > 1: # Keep placeholder if no achievements
             item = self.achievements_layout.takeAt(0)
             if item.widget():
                 item.widget().deleteLater()

        if achievements:
            self.achievements_placeholder.hide()
            # TODO: Add widgets for each achievement
            # for achievement in achievements:
            #     achievement_label = QLabel(f"徽章: {achievement['name']}")
            #     self.achievements_layout.addWidget(achievement_label)
            pass # Placeholder for actual implementation
        else:
            self.achievements_placeholder.setText("暂无成就，继续努力吧！")
            self.achievements_placeholder.show()

    def clear_achievements(self):
        """Clear the achievements display area."""
         # Clear previous achievements (if any)
        while self.achievements_layout.count() > 1:
             item = self.achievements_layout.takeAt(0)
             if item.widget():
                 item.widget().deleteLater()
        self.achievements_placeholder.setText("成就徽章将在此处展示。")
        self.achievements_placeholder.show()
