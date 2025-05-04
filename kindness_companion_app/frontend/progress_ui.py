from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QCalendarWidget, QComboBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QMessageBox,
    QGroupBox, QSpacerItem, QProgressBar, QScrollArea, QTextEdit # Add QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QDate, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QTextCharFormat, QBrush

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox

# Import AI report generator
try:
    from ai_core.report_generator import generate_weekly_report
except ImportError:
    logging.error("Could not import generate_weekly_report. AI report features will be disabled.")
    generate_weekly_report = None  # type: ignore

import datetime
import logging


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
        self.weekly_report_text = ""
        self.report_last_generated = None

        # Initialize UI attributes to None for clarity
        self.main_layout = None
        self.header_layout = None
        self.title_label = None
        self.filter_layout = None
        self.challenge_label = None
        self.challenge_combo = None
        self.range_label = None
        self.range_combo = None
        self.main_content_layout = None
        self.left_panel_widget = None # Initialize here
        self.left_panel_layout = None
        self.calendar_widget = None
        self.stats_group = None
        self.stats_layout = None
        self.total_label = None
        self.streak_label = None
        self.rate_label = None
        self.weekly_report_group = None
        self.weekly_report_text_edit = None
        self.generate_report_button = None
        self.achievements_group = None
        self.achievements_scroll_area = None
        self.achievements_container = None
        self.achievements_layout = None
        self.achievements_placeholder = None
        self.achievements_spacer = None
        self.progress_table = None

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

        # --- Left Panel ---\n        self.left_panel_widget = QWidget()
        self.left_panel_widget = QWidget()
        logging.debug(f"Value of self.left_panel_widget before setObjectName: {self.left_panel_widget}") # Add logging here
        self.left_panel_widget.setObjectName("left_panel")
        self.left_panel_layout = QVBoxLayout(self.left_panel_widget)
        self.left_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.left_panel_layout.setSpacing(15)
        self.left_panel_widget.setMaximumWidth(350)

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

        # Weekly Report GroupBox
        self.weekly_report_group = QGroupBox("AI 周报")
        self.weekly_report_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        weekly_report_layout = QVBoxLayout(self.weekly_report_group)

        # Report text area
        self.weekly_report_text_edit = QTextEdit()
        self.weekly_report_text_edit.setReadOnly(True)
        self.weekly_report_text_edit.setPlaceholderText("点击下方按钮生成本周善行报告...")
        self.weekly_report_text_edit.setMinimumHeight(100)
        self.weekly_report_text_edit.setMaximumHeight(150)
        self.weekly_report_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        weekly_report_layout.addWidget(self.weekly_report_text_edit)

        # Generate report button
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        self.generate_report_button = QPushButton("生成周报")
        self.generate_report_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.generate_report_button.clicked.connect(self.generate_weekly_report)
        button_layout.addWidget(self.generate_report_button)
        weekly_report_layout.addLayout(button_layout)

        self.left_panel_layout.addWidget(self.weekly_report_group)

        # Achievements GroupBox - Now contains the ScrollArea
        self.achievements_group = QGroupBox("我的成就")
        self.achievements_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding) # Allow groupbox to expand
        achievements_group_layout = QVBoxLayout(self.achievements_group) # Layout for the groupbox itself
        achievements_group_layout.setContentsMargins(5, 5, 5, 5) # Add some padding inside the groupbox

        # Create Scroll Area for achievements
        self.achievements_scroll_area = QScrollArea()
        self.achievements_scroll_area.setWidgetResizable(True) # Important! Allows inner widget to resize
        self.achievements_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # No horizontal scroll
        self.achievements_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # Show vertical scroll when needed
        self.achievements_scroll_area.setFrameShape(QFrame.NoFrame) # Remove scroll area border if desired

        # Create a container widget for the achievements layout
        self.achievements_container = QWidget()
        self.achievements_layout = QVBoxLayout(self.achievements_container) # The actual layout for achievements
        self.achievements_layout.setAlignment(Qt.AlignTop) # Align items to the top
        self.achievements_layout.setSpacing(8) # Spacing between achievements

        # Add placeholder to the achievements layout
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setAlignment(Qt.AlignCenter)
        self.achievements_layout.addWidget(self.achievements_placeholder)

        # Add a spacer item at the end of the achievements layout to push content up
        self.achievements_spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.achievements_layout.addSpacerItem(self.achievements_spacer)

        # Set the container widget for the scroll area
        self.achievements_scroll_area.setWidget(self.achievements_container)

        # Add the scroll area to the groupbox layout
        achievements_group_layout.addWidget(self.achievements_scroll_area)

        # Add Achievements GroupBox to Left Panel Layout
        self.left_panel_layout.addWidget(self.achievements_group)

        # Add Left Panel to Main Content Layout
        self.main_content_layout.addWidget(self.left_panel_widget, 1)

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

        # Reset weekly report
        self.weekly_report_text_edit.setText("点击下方按钮生成本周善行报告...")
        self.weekly_report_text = ""
        self.report_last_generated = None

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
        """Load and display user achievements/badges within a scroll area."""
        if not self.current_user:
            return

        user_id = self.current_user["id"]

        # --- Fetch achievement data (remains the same) ---
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(user_id)
        subscribed_challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(subscribed_challenges)
        eco_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "环保")
        community_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "社区服务")

        # --- Define achievements_data (remains the same) ---
        achievements_data = [
            # --- Check-in Milestones ---
            {"name": "善行初学者", "target": 10, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善行践行者", "target": 50, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善意大师", "target": 100, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},

            # --- Streak Milestones ---
            {"name": "坚持不懈", "target": 7, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "毅力之星", "target": 14, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "恒心典范", "target": 30, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},

            # --- Subscription Milestones ---
            {"name": "探索之心", "target": 5, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "挑战收藏家", "target": 10, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "领域专家", "target": 20, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},

            # --- Category Milestones ---
            {"name": "环保卫士", "target": 10, "current": eco_check_ins, "unit": "次环保行动", "icon": ":/icons/leaf.svg"},
            {"name": "社区之星", "target": 10, "current": community_check_ins, "unit": "次社区服务", "icon": ":/icons/users.svg"}, # Assuming users.svg exists

            # --- Generic Target Milestone ---
            {"name": "目标达成者", "target": 25, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/target.svg"}, # Example using target.svg
            {"name": "闪耀新星", "target": 15, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/star.svg"}, # Example using star.svg
        ]

        # --- Clear previous achievements ---
        self.clear_achievements() # Call the improved clear method first

        achievements_added = False
        # --- Populate achievements layout ---
        for ach in achievements_data:
            if ach["target"] > 0:
                achievements_added = True
                ach_layout = QHBoxLayout()
                ach_layout.setSpacing(10)

                # Icon Label (Optional)
                icon_label = QLabel()
                icon_path = ach.get("icon", None) # Get icon path, default to None
                if icon_path:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                         # Scale icon for display
                         pixmap = icon.pixmap(QSize(20, 20)) # Adjust size as needed
                         icon_label.setPixmap(pixmap)
                    else:
                         logging.warning(f"Failed to load achievement icon: {icon_path}")
                         icon_label.setText("?") # Placeholder if icon fails
                         icon_label.setFixedSize(20, 20)
                         icon_label.setAlignment(Qt.AlignCenter)
                else:
                    icon_label.setFixedSize(20, 20) # Keep space consistent even without icon

                icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                ach_layout.addWidget(icon_label)


                title_label = QLabel(ach["name"])
                title_label.setMinimumWidth(70) # Adjust width if needed with icon
                title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

                progress_bar = QProgressBar()
                progress_bar.setRange(0, ach['target'])
                display_value = min(ach['current'], ach['target'])
                progress_bar.setValue(display_value)
                progress_bar.setFormat(f"{display_value}/{ach['target']} {ach['unit']}") # Simplified format
                progress_bar.setAlignment(Qt.AlignCenter)
                progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

                # --- Styling (remains the same) ---
                if ach["current"] >= ach["target"]:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                    """)
                else:
                     progress_bar.setStyleSheet("""
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                        QProgressBar::chunk { background-color: #2196F3; border-radius: 4px; width: 10px; margin: 0.5px; }
                     """)

                ach_layout.addWidget(title_label)
                ach_layout.addWidget(progress_bar)

                # Insert the new achievement layout *before* the spacer in achievements_layout
                insert_index = self.achievements_layout.count() - 1 # Index before the spacer
                self.achievements_layout.insertLayout(insert_index, ach_layout)

        # --- Manage placeholder visibility ---
        if achievements_added:
            self.achievements_placeholder.hide()
            self.achievements_spacer.changeSize(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) # Ensure spacer pushes content up
        else:
            self.achievements_placeholder.setText("暂无成就，继续努力吧！")
            self.achievements_placeholder.show()
            self.achievements_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed) # Collapse spacer if no achievements


    def generate_weekly_report(self):
        """Generate and display a weekly AI report for the user."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "无法生成报告", "请先登录")
            return

        if not generate_weekly_report:
            AnimatedMessageBox.showWarning(
                self,
                "功能不可用",
                "AI 报告功能不可用。请确保 AI 核心模块已正确安装。"
            )
            return

        # --- AI Consent Check Removed ---
        # Consent is now assumed True by default
        user_id = self.current_user.get('id')
        logger.info(f"AI consent assumed True for user {user_id}. Proceeding with report generation.")
        # --- End AI Consent Check Removed ---

        # Show loading state
        self.report_text_edit.setPlainText("正在生成报告，请稍候...")
        self.generate_report_button.setEnabled(False)

        # Call the AI report generator in a separate thread
        try:
            # Fetch recent progress data
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=7)
            progress_data = self.progress_tracker.get_check_ins_between_dates(
                user_id, start_date.isoformat(), end_date.isoformat()
            )

            # Prepare data for AI
            report_input = {
                "user_id": user_id,
                "username": self.current_user.get("username", "用户"),
                "progress_data": progress_data,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

            # Run AI generation in a thread
            self.report_thread = AIReportThread(generate_weekly_report, report_input)
            self.report_thread.report_ready.connect(self.display_report)
            self.report_thread.report_error.connect(self.display_report_error)
            self.report_thread.start()

        except Exception as e:
            logger.error(f"Error preparing data for weekly report: {e}", exc_info=True)
            self.display_report_error(f"准备报告数据时出错: {e}")

    def clear_achievements(self):
        """Safely clear the achievements display area, preserving placeholder and spacer."""
        if not self.achievements_layout:
            logging.error("clear_achievements called but achievements_layout is None.")
            return

        items_to_remove = []
        # Identify items to remove (excluding placeholder widget and spacer item)
        for i in range(self.achievements_layout.count()):
            item = self.achievements_layout.itemAt(i)
            if item:
                widget = item.widget()
                spacer = item.spacerItem()
                # Check if it's NOT the placeholder widget AND NOT the spacer item
                if widget != self.achievements_placeholder and not spacer:
                    items_to_remove.append(item)
                # Also check if it's a layout item that doesn't contain the placeholder
                elif item.layout() is not None:
                     # We assume achievement items are layouts, placeholder is a direct widget
                     items_to_remove.append(item)

        # Remove identified items and delete their contents
        for item in items_to_remove:
            self.achievements_layout.removeItem(item)
            layout = item.layout()
            if layout is not None:
                # Delete widgets within the layout
                while layout.count():
                    child_item = layout.takeAt(0)
                    if child_item:
                        child_widget = child_item.widget()
                        if child_widget:
                            child_widget.deleteLater()
                # Delete the layout itself after clearing children
                # layout.deleteLater() # removeItem should detach it, Python GC handles layout object
            else:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            # del item # Let Python GC handle the QLayoutItem object

        # After clearing, ensure placeholder is valid and visible
        try:
            # Check if the C++ object still exists before accessing it
            if self.achievements_placeholder and self.achievements_placeholder.parent(): # Check if it's still part of a valid hierarchy
                self.achievements_placeholder.setText("成就徽章将在此处展示。")
                self.achievements_placeholder.show()
                # Find and collapse spacer
                for i in range(self.achievements_layout.count()):
                    item = self.achievements_layout.itemAt(i)
                    if item and item.spacerItem():
                        item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
                        break
            else:
                logging.warning("clear_achievements: achievements_placeholder seems invalid or deleted.")
                # Optionally recreate placeholder if necessary, though this indicates a deeper issue
                # self.achievements_placeholder = QLabel("成就徽章将在此处展示。")
                # self.achievements_layout.insertWidget(0, self.achievements_placeholder) # Re-add if needed

        except RuntimeError as e:
            # Catch the specific error if the check somehow fails
            logging.error(f"RuntimeError in clear_achievements accessing placeholder: {e}")

# ... (rest of the class) ...
