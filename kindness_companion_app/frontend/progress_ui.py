import datetime
import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QCalendarWidget,
    QComboBox,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QSpacerItem,
    QProgressBar,
    QScrollArea,
    QTextEdit,
    QListWidget,
    QListWidgetItem,  # Add QListWidget and QListWidgetItem
    QTabWidget,
    QBoxLayout,
    QLayout,  # 添加QLayout导入
    QDialog,
    QDialogButtonBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QDate, QSize, QTimer, QThread, QMargins
from PySide6.QtGui import (
    QFont,
    QColor,
    QIcon,
    QTextCharFormat,
    QBrush,
    QPainter,
)
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QPieSeries,
    QPieSlice,
)

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox

# Import AI report generator
try:
    from kindness_companion_app.ai_core.report_generator import generate_weekly_report
except ImportError:
    logging.error(
        "Could not import generate_weekly_report. AI report features will be disabled."
    )
    generate_weekly_report = None  # type: ignore


class AIReportThread(QThread):
    """Thread for generating AI reports without blocking the UI."""

    report_ready = Signal(str)
    report_error = Signal(str)

    def __init__(self, generator_func, report_input):
        """
        Initialize the thread with the generator function and input data.

        Args:
            generator_func: Function to call for report generation
            report_input: Dictionary of input data for the generator
        """
        super().__init__()
        self.generator_func = generator_func
        self.report_input = report_input

    def run(self):
        """Run the report generation in a separate thread."""
        try:
            if self.generator_func:
                report = self.generator_func(self.report_input)
                self.report_ready.emit(report)
            else:
                self.report_error.emit("报告生成功能不可用")
        except Exception as e:
            logging.error(f"Error in AI report thread: {e}", exc_info=True)
            self.report_error.emit(f"生成报告时出错: {e}")


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
        self.report_history = []  # Store report history
        self.ai_report_generator = None  # Initialize AI report generator

        # 添加图表相关属性
        self.pie_chart = None
        self.pie_view = None

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
        self.left_panel_widget = None  # Initialize here
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
        self.bottom_split_widget = None
        self.bottom_split = None

        self.setup_ui()

    def setup_ui(self):
        """重构打卡记录界面布局，提升美观性和信息层次。"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 28, 28, 28)
        self.main_layout.setSpacing(22)
        self.main_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)

        # 设置整体大小策略
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # 顶部标题与筛选器
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        self.title_label = QLabel("打卡记录")
        self.title_label.setObjectName("title_label")
        self.title_label.setFont(QFont("Hiragino Sans GB", 22, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        self.challenge_label = QLabel("挑战:")
        self.challenge_combo = QComboBox()
        self.challenge_combo.setFixedWidth(160)
        self.challenge_combo.addItem("全部挑战", None)
        self.challenge_combo.currentIndexChanged.connect(self.load_progress)
        header_layout.addWidget(self.challenge_label)
        header_layout.addWidget(self.challenge_combo)
        self.range_label = QLabel("时间范围:")
        self.range_combo = QComboBox()
        self.range_combo.setFixedWidth(120)
        self.range_combo.addItem("最近7天", 7)
        self.range_combo.addItem("最近30天", 30)
        self.range_combo.addItem("最近90天", 90)
        self.range_combo.addItem("全部记录", None)
        self.range_combo.currentIndexChanged.connect(self.load_progress)
        header_layout.addWidget(self.range_label)
        header_layout.addWidget(self.range_combo)
        self.main_layout.addLayout(header_layout)

        # 主内容区：左右分栏
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(32)

        # 左侧：日历+统计
        left_panel = QVBoxLayout()
        left_panel.setSpacing(24)
        # 日历
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setObjectName("calendar_widget")
        self.calendar_widget.setFixedHeight(220)
        self.calendar_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.calendar_widget.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar_widget.setSelectionMode(
            QCalendarWidget.SelectionMode.SingleSelection
        )
        self.calendar_widget.clicked.connect(self.calendar_date_clicked)
        left_panel.addWidget(self.calendar_widget)
        # 统计数据
        stats_group = QGroupBox("统计数据")
        stats_group.setObjectName("stats_group")
        stats_group.setMinimumHeight(540)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(16, 18, 16, 12)
        stats_layout.setSpacing(10)

        # 基础统计信息
        basic_stats_layout = QHBoxLayout()
        self.total_label = QLabel("总打卡次数: 0")
        self.total_label.setObjectName("stat_label")
        self.streak_label = QLabel("当前连续打卡: 0 天")
        self.streak_label.setObjectName("stat_label")
        self.rate_label = QLabel("完成率: 0%")
        self.rate_label.setObjectName("stat_label")
        basic_stats_layout.addWidget(self.total_label)
        basic_stats_layout.addWidget(self.streak_label)
        basic_stats_layout.addWidget(self.rate_label)
        stats_layout.addLayout(basic_stats_layout)

        # 添加图表容器
        charts_layout = QVBoxLayout()

        # 饼图：显示各类别占比
        self.pie_chart = QChart()
        self.pie_chart.setTitle("挑战类别分布")
        self.pie_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.pie_chart.legend().setVisible(True)
        self.pie_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)

        self.pie_view = QChartView(self.pie_chart)
        self.pie_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.pie_view.setMinimumHeight(320)
        self.pie_view.setMaximumHeight(400)
        self.pie_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        charts_layout.addWidget(self.pie_view)

        stats_layout.addLayout(charts_layout)
        stats_layout.addStretch()
        left_panel.addWidget(stats_group)
        left_panel.addStretch()
        main_content_layout.addLayout(left_panel, 1)

        # 右侧：表格+AI周报+成就
        right_panel = QVBoxLayout()
        right_panel.setSpacing(18)
        self.progress_table = QTableWidget()
        self.progress_table.setObjectName("progress_table")
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(["日期", "挑战", "分类", "操作"])
        header = self.progress_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.progress_table.setColumnWidth(0, 120)
        self.progress_table.setColumnWidth(2, 110)
        self.progress_table.setColumnWidth(3, 100)
        self.progress_table.verticalHeader().setVisible(False)
        self.progress_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.progress_table.verticalHeader().setDefaultSectionSize(44)
        self.progress_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.progress_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.progress_table.setAlternatingRowColors(True)
        self.progress_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.progress_table.setMinimumHeight(260)
        right_panel.addWidget(self.progress_table, 3)
        # 横向分栏（AI周报+成就）
        self.bottom_split = QHBoxLayout()
        self.bottom_split.setSpacing(18)
        ai_group = QGroupBox("AI 周报")
        ai_group.setObjectName("weekly_report_group")
        ai_group.setMinimumWidth(260)
        ai_group.setMinimumHeight(180)
        ai_group.setVisible(True)
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setContentsMargins(14, 18, 14, 14)
        ai_layout.setSpacing(10)
        self.weekly_report_text_edit = QTextEdit()
        self.weekly_report_text_edit.setReadOnly(True)
        self.weekly_report_text_edit.setPlaceholderText(
            "点击下方按钮生成本周善行报告..."
        )
        self.weekly_report_text_edit.setMinimumHeight(70)
        self.weekly_report_text_edit.setMaximumHeight(110)
        ai_layout.addWidget(self.weekly_report_text_edit)
        self.report_progress_bar = QProgressBar()
        self.report_progress_bar.setVisible(False)
        self.report_progress_bar.setRange(0, 0)  # Indeterminate progress
        self.report_progress_bar.setTextVisible(False)
        ai_layout.addWidget(self.report_progress_bar)
        ai_btn_layout = QHBoxLayout()
        ai_btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.generate_report_button = QPushButton("生成周报")
        self.generate_report_button.setObjectName("generate_report_button")
        self.generate_report_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.generate_report_button.setFixedSize(110, 32)
        self.generate_report_button.clicked.connect(self.generate_weekly_report)
        ai_btn_layout.addWidget(self.generate_report_button)
        self.history_button = QPushButton("历史记录")
        self.history_button.setObjectName("history_button")
        self.history_button.setIcon(QIcon(":/icons/history.svg"))
        self.history_button.setFixedSize(110, 32)
        self.history_button.clicked.connect(self.show_report_history)
        ai_btn_layout.addWidget(self.history_button)
        ai_layout.addLayout(ai_btn_layout)
        ai_group.setLayout(ai_layout)
        self.bottom_split.addWidget(ai_group, 1)
        # 成就显示
        achievements_group = QGroupBox("我的成就")
        achievements_group.setObjectName("achievements_group")
        achievements_group.setMinimumWidth(260)
        achievements_group.setMinimumHeight(180)
        achievements_group.setVisible(True)
        achievements_layout = QVBoxLayout(achievements_group)
        achievements_layout.setContentsMargins(14, 18, 14, 14)
        achievements_layout.setSpacing(10)
        self.achievements_scroll_area = QScrollArea()
        self.achievements_scroll_area.setWidgetResizable(True)
        self.achievements_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.achievements_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.achievements_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.achievements_container = QWidget()
        self.achievements_layout = QVBoxLayout(self.achievements_container)
        self.achievements_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.achievements_layout.setSpacing(10)
        self.achievements_layout.setContentsMargins(4, 4, 4, 4)
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.achievements_placeholder.setObjectName("achievements_placeholder")
        self.achievements_layout.addWidget(self.achievements_placeholder)
        self.achievements_spacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.achievements_layout.addSpacerItem(self.achievements_spacer)
        self.achievements_scroll_area.setWidget(self.achievements_container)
        achievements_layout.addWidget(self.achievements_scroll_area)
        self.bottom_split.addWidget(achievements_group, 1)
        bottom_split_widget = QWidget()
        bottom_split_widget.setLayout(self.bottom_split)
        bottom_split_widget.setMinimumHeight(220)
        right_panel.addWidget(bottom_split_widget, 2)
        main_content_layout.addLayout(right_panel, 2)
        self.main_layout.addLayout(main_content_layout)

        # 设置表格行高固定且充足
        self.progress_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.progress_table.verticalHeader().setDefaultSectionSize(44)
        # 保证AI周报与成就区块强制显示
        ai_group.setVisible(True)
        achievements_group.setVisible(True)

    def resizeEvent(self, event):
        width = self.width()

        # Get the main content layout
        main_content_layout = None
        if self.main_layout is not None:
            for i in range(self.main_layout.count()):
                item = self.main_layout.itemAt(i)
                if item and item.layout():
                    main_content_layout = item.layout()
                    break

        if main_content_layout is not None:
            if width < 1000:  # 窄屏布局
                if isinstance(main_content_layout, QBoxLayout):
                    main_content_layout.setDirection(QBoxLayout.Direction.TopToBottom)
                    # 移除横向分栏
                    for i in range(main_content_layout.count()):
                        item = main_content_layout.itemAt(i)
                        if (
                            item is not None
                            and item.layout() is not None
                            and item.layout() is self.bottom_split
                        ):
                            if self.bottom_split is not None:
                                main_content_layout.removeItem(item)
                            break
                    # 添加纵向分栏
                    if self.bottom_split is not None:
                        main_content_layout.addLayout(self.bottom_split)
                self.setStyleSheet(
                    "font-size: 13px; QGroupBox {margin-top: 8px;} QTableWidget {font-size: 12px;}"
                )
                if self.progress_table is not None:
                    self.progress_table.setMinimumHeight(180)
            else:  # 宽屏布局
                if isinstance(main_content_layout, QBoxLayout):
                    main_content_layout.setDirection(QBoxLayout.Direction.LeftToRight)
                    # 移除纵向分栏
                    for i in range(main_content_layout.count()):
                        item = main_content_layout.itemAt(i)
                        if (
                            item is not None
                            and item.layout() is not None
                            and item.layout() is self.bottom_split
                        ):
                            if self.bottom_split is not None:
                                main_content_layout.removeItem(item)
                            break
                    # 添加横向分栏
                    if self.bottom_split is not None:
                        main_content_layout.addLayout(self.bottom_split)
                self.setStyleSheet(
                    "font-size: 15px; QGroupBox {margin-top: 14px;} QTableWidget {font-size: 14px;}"
                )
                if self.progress_table is not None:
                    self.progress_table.setMinimumHeight(260)

        super().resizeEvent(event)

    @Slot(dict)
    def set_user(self, user):
        """Set the current user and update the UI accordingly."""
        self.current_user = user
        if user:
            # 初始化 AI 报告生成器
            from ..ai_core.report_generator import generate_weekly_report

            self.ai_report_generator = generate_weekly_report

            # 加载用户数据
            self.load_user_challenges()
            self.load_progress()
            self.load_achievements()
        else:
            self.clear_progress()
            self.clear_achievements()

    def load_user_challenges(self):
        """Load user's subscribed challenges."""
        if not self.current_user:
            return

        challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])

        if self.challenge_combo is not None:
            self.challenge_combo.clear()
            combo = self.challenge_combo
            if combo is not None:
                combo.addItem("全部挑战", None)

        for challenge in challenges:
            if self.challenge_combo is not None:
                self.challenge_combo.addItem(challenge["title"], challenge["id"])

    def load_progress(self):
        """Load and display progress."""
        if not self.current_user:
            return

        if self.challenge_combo is not None:
            challenge_id = self.challenge_combo.currentData()
        else:
            challenge_id = None
        days = self.range_combo.currentData() if self.range_combo is not None else None

        end_date = datetime.date.today()
        start_date = None
        if days:
            start_date = end_date - datetime.timedelta(days=days - 1)

        if challenge_id:
            check_ins = self.progress_tracker.get_check_ins(
                self.current_user["id"],
                challenge_id,
                start_date.isoformat() if start_date else None,
                end_date.isoformat(),
            )
            streak = self.progress_tracker.get_streak(
                self.current_user["id"], challenge_id
            )
            rate = self.progress_tracker.get_completion_rate(
                self.current_user["id"],
                challenge_id,
                days or 30,  # Default to 30 days for rate if 'All' selected
            )
            if self.total_label is not None:
                self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            if self.streak_label is not None:
                self.streak_label.setText(f"当前连续打卡: {streak} 天")
            if self.rate_label is not None:
                self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
        else:
            check_ins = self.progress_tracker.get_all_user_check_ins(
                self.current_user["id"],
                start_date.isoformat() if start_date else None,
                end_date.isoformat(),
            )
            unique_dates = set(ci["check_in_date"] for ci in check_ins)
            if self.total_label is not None:
                self.total_label.setText(f"总打卡次数: {len(check_ins)}")
            if self.streak_label is not None:
                self.streak_label.setText(
                    "当前连续打卡: - 天"
                )  # Streak is challenge-specific
            if days:
                # Calculate rate based on unique days checked in within the period
                rate = len(unique_dates) / days if days > 0 else 0
                if self.rate_label is not None:
                    self.rate_label.setText(f"完成率: {rate * 100:.1f}%")
            else:
                if self.rate_label is not None:
                    self.rate_label.setText(
                        "完成率: - %"
                    )  # Rate doesn't make sense for 'All'

        self.update_calendar(check_ins)
        self.update_table(check_ins)
        self.load_achievements()
        self.update_charts(check_ins)

    def update_calendar(self, check_ins):
        """Update the calendar view with check-in dates."""
        # Clear previous formatting by setting a default format for a null date
        default_format = QTextCharFormat()
        if self.calendar_widget is not None and hasattr(
            self.calendar_widget, "setDateTextFormat"
        ):
            self.calendar_widget.setDateTextFormat(QDate(), default_format)

        # Highlight check-in dates
        check_in_format = QTextCharFormat()
        check_in_format.setBackground(
            QBrush(QColor("#A5D6A7"))
        )  # Use a theme-friendly color
        check_in_format.setForeground(
            QBrush(QColor("#212121"))
        )  # Ensure text is readable

        check_in_dates = {
            QDate.fromString(ci["check_in_date"], "yyyy-MM-dd") for ci in check_ins
        }

        # Iterate through visible month to apply/clear formats efficiently
        if self.calendar_widget is not None and hasattr(
            self.calendar_widget, "monthShown"
        ):
            current_month = self.calendar_widget.monthShown()
            current_year = self.calendar_widget.yearShown()
        else:
            current_month = QDate.currentDate().month()
            current_year = QDate.currentDate().year()
        start_date = QDate(current_year, current_month, 1)
        end_date = start_date.addMonths(1).addDays(-1)

        date_iter = start_date
        while date_iter <= end_date:
            if self.calendar_widget is not None and hasattr(
                self.calendar_widget, "dateTextFormat"
            ):
                existing_format = self.calendar_widget.dateTextFormat(date_iter)
            else:
                existing_format = QTextCharFormat()
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

            if self.calendar_widget is not None and hasattr(
                self.calendar_widget, "setDateTextFormat"
            ):
                self.calendar_widget.setDateTextFormat(date_iter, existing_format)
            date_iter = date_iter.addDays(1)

    def update_table(self, check_ins):
        """
        Update the table with check-in records.

        Args:
            check_ins (list): List of check-in dictionaries
        """
        if self.progress_table is not None:
            self.progress_table.setRowCount(0)

        # Sort check-ins by date descending
        sorted_check_ins = sorted(
            check_ins, key=lambda x: x["check_in_date"], reverse=True
        )

        for i, check_in in enumerate(sorted_check_ins):
            if self.progress_table is not None:
                self.progress_table.insertRow(i)

            date_str = check_in["check_in_date"]
            try:
                date_obj = datetime.date.fromisoformat(date_str)
                formatted_date = date_obj.strftime("%Y-%m-%d (%a)")
            except ValueError:
                formatted_date = date_str  # Fallback if format is wrong
            date_item = QTableWidgetItem(formatted_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.progress_table is not None:
                self.progress_table.setItem(i, 0, date_item)

            challenge_title = check_in.get("challenge_title")
            if not challenge_title:
                challenge = self.challenge_manager.get_challenge_by_id(
                    check_in["challenge_id"]
                )
                challenge_title = challenge["title"] if challenge else "未知挑战"
            challenge_item = QTableWidgetItem(challenge_title)
            if self.progress_table is not None:
                self.progress_table.setItem(i, 1, challenge_item)

            category = check_in.get("category")
            if not category:
                challenge = self.challenge_manager.get_challenge_by_id(
                    check_in["challenge_id"]
                )
                category = challenge["category"] if challenge else "未知分类"
            category_item = QTableWidgetItem(category)
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.progress_table is not None:
                self.progress_table.setItem(i, 2, category_item)

            # Action button (Undo)
            button_widget = QWidget()  # Use a container widget for centering
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)  # Small margins
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            undo_button = QPushButton("撤销")
            undo_button.setObjectName("undo_button")
            undo_button.setIcon(QIcon(":/icons/rotate-ccw.svg"))
            undo_button.setIconSize(QSize(16, 16))
            undo_button.setFixedSize(QSize(80, 28))  # Fixed size for consistency
            undo_button.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            undo_button.clicked.connect(
                lambda checked=False, ci=check_in: self.undo_check_in(ci)
            )
            button_layout.addWidget(undo_button)
            if self.progress_table is not None:
                self.progress_table.setCellWidget(i, 3, button_widget)

        # Adjust row heights after populating
        if self.progress_table is not None:
            self.progress_table.resizeRowsToContents()

    def clear_progress(self):
        """Clear progress display."""
        if self.challenge_combo is not None:
            self.challenge_combo.clear()
            self.challenge_combo.addItem("全部挑战", None)

        # Reset calendar formatting
        self.update_calendar([])  # Update with empty list to clear highlights

        if self.progress_table is not None:
            self.progress_table.setRowCount(0)

        if self.total_label is not None:
            self.total_label.setText("总打卡次数: 0")
        if self.streak_label is not None:
            self.streak_label.setText("当前连续打卡: 0 天")
        if self.rate_label is not None:
            self.rate_label.setText("完成率: 0%")

        # Reset weekly report
        if self.weekly_report_text_edit is not None:
            self.weekly_report_text_edit.setPlainText("点击下方按钮生成本周善行报告...")
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
        if self.challenge_combo is not None:
            challenge_id = self.challenge_combo.currentData()
        else:
            challenge_id = None

        # Get check-ins specifically for the clicked date
        if challenge_id:
            check_ins = self.progress_tracker.get_check_ins(
                self.current_user["id"], challenge_id, date_str, date_str
            )
        else:
            check_ins = self.progress_tracker.get_all_user_check_ins(
                self.current_user["id"], date_str, date_str
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
        print("[UI] 开始撤销打卡操作")
        print(f"[UI] 撤销打卡参数: {check_in}")

        if not self.current_user:
            print("[UI] 错误: 用户未登录")
            return

        challenge = self.challenge_manager.get_challenge_by_id(check_in["challenge_id"])
        challenge_title = challenge["title"] if challenge else "未知挑战"
        print(f"[UI] 获取到挑战信息: {challenge_title}")

        # 确保日期为字符串且只取日期部分
        date_str = check_in["check_in_date"]
        print(f"[UI] 原始日期值: {date_str}, 类型: {type(date_str)}")

        if isinstance(date_str, datetime.date):
            date_str = date_str.isoformat()
            print(f"[UI] 转换日期对象为字符串: {date_str}")
        elif isinstance(date_str, str):
            date_str = date_str[:10]  # 只取YYYY-MM-DD
            print(f"[UI] 截取日期字符串: {date_str}")
        else:
            print(f"[UI] 警告: 未知的日期类型: {type(date_str)}")
            return

        print(f"[UI] 最终使用的日期: {date_str}")

        reply = AnimatedMessageBox.showQuestion(
            self.window(),
            "撤销打卡",
            f"确定要撤销 {date_str} 的 {challenge_title} 打卡记录吗？\n"
            f"这可能会影响您的连续打卡天数和成就。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("[UI] 用户确认撤销")
            success = self.progress_tracker.undo_check_in(
                self.current_user["id"],
                check_in["challenge_id"],
                date_str,
            )

            if success:
                print("[UI] 撤销成功")
                AnimatedMessageBox.showInformation(
                    self.window(), "操作成功", "打卡记录已撤销。"
                )
                self.load_progress()
            else:
                print("[UI] 撤销失败")
                AnimatedMessageBox.showWarning(
                    self.window(), "操作失败", "无法撤销打卡记录，请稍后再试。"
                )
        else:
            print("[UI] 用户取消撤销")

    def load_achievements(self):
        """Load and display user achievements/badges within a scroll area."""
        if not self.current_user:
            return

        user_id = self.current_user["id"]

        # --- Fetch achievement data (remains the same) ---
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(
            user_id
        )
        subscribed_challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(subscribed_challenges)
        eco_check_ins = self.progress_tracker.get_check_ins_count_by_category(
            user_id, "环保"
        )
        community_check_ins = self.progress_tracker.get_check_ins_count_by_category(
            user_id, "社区服务"
        )

        # --- Define achievements_data (remains the same) ---
        achievements_data = [
            # --- Check-in Milestones ---
            {
                "name": "善行初学者",
                "target": 10,
                "current": total_check_ins,
                "unit": "次打卡",
                "icon": ":/icons/award.svg",
            },
            {
                "name": "善行践行者",
                "target": 50,
                "current": total_check_ins,
                "unit": "次打卡",
                "icon": ":/icons/award.svg",
            },
            {
                "name": "善意大师",
                "target": 100,
                "current": total_check_ins,
                "unit": "次打卡",
                "icon": ":/icons/award.svg",
            },
            # --- Streak Milestones ---
            {
                "name": "坚持不懈",
                "target": 7,
                "current": longest_streak,
                "unit": "天连胜",
                "icon": ":/icons/zap.svg",
            },
            {
                "name": "毅力之星",
                "target": 14,
                "current": longest_streak,
                "unit": "天连胜",
                "icon": ":/icons/zap.svg",
            },
            {
                "name": "恒心典范",
                "target": 30,
                "current": longest_streak,
                "unit": "天连胜",
                "icon": ":/icons/zap.svg",
            },
            # --- Subscription Milestones ---
            {
                "name": "探索之心",
                "target": 5,
                "current": subscribed_challenges_count,
                "unit": "个挑战",
                "icon": ":/icons/book-open.svg",
            },
            {
                "name": "挑战收藏家",
                "target": 10,
                "current": subscribed_challenges_count,
                "unit": "个挑战",
                "icon": ":/icons/book-open.svg",
            },
            {
                "name": "领域专家",
                "target": 20,
                "current": subscribed_challenges_count,
                "unit": "个挑战",
                "icon": ":/icons/book-open.svg",
            },
            # --- Category Milestones ---
            {
                "name": "环保卫士",
                "target": 10,
                "current": eco_check_ins,
                "unit": "次环保行动",
                "icon": ":/icons/leaf.svg",
            },
            {
                "name": "社区之星",
                "target": 10,
                "current": community_check_ins,
                "unit": "次社区服务",
                "icon": ":/icons/users.svg",
            },  # Assuming users.svg exists
            # --- Generic Target Milestone ---
            {
                "name": "目标达成者",
                "target": 25,
                "current": total_check_ins,
                "unit": "次打卡",
                "icon": ":/icons/target.svg",
            },  # Example using target.svg
            {
                "name": "闪耀新星",
                "target": 15,
                "current": longest_streak,
                "unit": "天连胜",
                "icon": ":/icons/star.svg",
            },  # Example using star.svg
        ]

        # --- Clear previous achievements ---
        self.clear_achievements()  # Call the improved clear method first

        achievements_added = False
        # --- Populate achievements layout ---
        for ach in achievements_data:
            if ach["target"] > 0:
                achievements_added = True
                ach_layout = QHBoxLayout()
                ach_layout.setSpacing(10)

                # Icon Label (Optional)
                icon_label = QLabel()
                icon_path = ach.get("icon", None)  # Get icon path, default to None
                if icon_path:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        # Scale icon for display
                        pixmap = icon.pixmap(QSize(20, 20))  # Adjust size as needed
                        icon_label.setPixmap(pixmap)
                    else:
                        logging.warning(f"Failed to load achievement icon: {icon_path}")
                        icon_label.setText("?")  # Placeholder if icon fails
                        icon_label.setFixedSize(20, 20)
                        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    icon_label.setFixedSize(
                        20, 20
                    )  # Keep space consistent even without icon

                icon_label.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                ach_layout.addWidget(icon_label)

                title_label = QLabel(ach["name"])
                title_label.setMinimumWidth(70)  # Adjust width if needed with icon
                title_label.setSizePolicy(
                    QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
                )

                progress_bar = QProgressBar()
                progress_bar.setRange(0, ach["target"])
                display_value = min(ach["current"], ach["target"])
                progress_bar.setValue(display_value)
                progress_bar.setFormat(
                    f"{display_value}/{ach['target']} {ach['unit']}"
                )  # Simplified format
                progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                progress_bar.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )

                # --- Styling (remains the same) ---
                if ach["current"] >= ach["target"]:
                    progress_bar.setStyleSheet(
                        """
                        QProgressBar::chunk { background-color: #4CAF50; border-radius: 4px; }
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                    """
                    )
                else:
                    progress_bar.setStyleSheet(
                        """
                        QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
                        QProgressBar::chunk { background-color: #2196F3; border-radius: 4px; width: 10px; margin: 0.5px; }
                     """
                    )

                ach_layout.addWidget(title_label)
                ach_layout.addWidget(progress_bar)

                # Insert the new achievement layout *before* the spacer in achievements_layout
                if self.achievements_layout is not None and hasattr(
                    self.achievements_layout, "count"
                ):
                    insert_index = self.achievements_layout.count() - 1
                    if hasattr(self.achievements_layout, "insertLayout"):
                        self.achievements_layout.insertLayout(insert_index, ach_layout)

        # --- Manage placeholder visibility ---
        if achievements_added:
            if self.achievements_placeholder is not None:
                self.achievements_placeholder.hide()
            if self.achievements_spacer is not None:
                self.achievements_spacer.changeSize(
                    20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
                )
        else:
            if self.achievements_placeholder is not None:
                self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                self.achievements_placeholder.show()
            if self.achievements_spacer is not None:
                self.achievements_spacer.changeSize(
                    0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
                )  # Collapse spacer if no achievements

    def generate_weekly_report(self):
        """Generate a weekly report using AI."""
        if not self.current_user:
            QMessageBox.warning(self, "提示", "请先登录后再生成报告")
            return

        if not hasattr(self, "ai_report_generator") or self.ai_report_generator is None:
            QMessageBox.warning(self, "提示", "AI报告生成功能不可用")
            return

        # 准备报告生成所需的数据
        report_input = {
            "user_id": self.current_user["id"],
            "username": self.current_user["username"],
            "start_date": (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).strftime("%Y-%m-%d"),
            "end_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        }

        # 更新UI状态
        if self.generate_report_button:
            self.generate_report_button.setEnabled(False)
            self.generate_report_button.setText("生成中...")
        if self.weekly_report_text_edit:
            self.weekly_report_text_edit.setPlainText("正在生成报告，请稍候...")
        if self.report_progress_bar:
            self.report_progress_bar.setVisible(True)

        # 创建并启动报告生成线程
        self.report_thread = AIReportThread(self.ai_report_generator, report_input)
        self.report_thread.report_ready.connect(self.display_report)
        self.report_thread.report_error.connect(self.display_report_error)
        self.report_thread.start()

    def display_report(self, report_text):
        """Display the generated AI report."""
        self.weekly_report_text = report_text
        if self.weekly_report_text_edit is not None:
            self.weekly_report_text_edit.setPlainText(report_text)
        self.report_last_generated = datetime.datetime.now()

        # 获取当前周的开始和结束日期
        current_week_start = self.report_last_generated.date() - datetime.timedelta(
            days=7
        )
        current_week_end = self.report_last_generated.date()
        current_week_range = f"{current_week_start} 至 {current_week_end}"

        # 保存周报到数据库
        if self.current_user:
            self.progress_tracker.save_weekly_report(
                self.current_user["id"],
                report_text,
                current_week_start.strftime("%Y-%m-%d"),
                current_week_end.strftime("%Y-%m-%d"),
            )

        # 更新UI状态
        if self.generate_report_button is not None:
            self.generate_report_button.setEnabled(True)
            self.generate_report_button.setText("生成周报")
        if self.report_progress_bar is not None:
            self.report_progress_bar.setVisible(False)

    def display_report_error(self, error_message):
        """Display an error message when report generation fails."""
        if self.weekly_report_text_edit is not None:
            self.weekly_report_text_edit.setPlainText(error_message)
        if self.generate_report_button is not None:
            self.generate_report_button.setEnabled(True)
        if self.report_progress_bar is not None:
            self.report_progress_bar.setVisible(False)

    def show_report_history(self):
        """显示周报历史记录"""
        if not self.current_user:
            QMessageBox.warning(self, "提示", "请先登录后再查看历史记录")
            return

        # 从数据库获取所有周报
        reports = self.progress_tracker.get_all_weekly_reports(self.current_user["id"])
        if not reports:
            QMessageBox.information(self, "提示", "暂无历史周报记录")
            return

        # 创建历史记录对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("周报历史记录")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # 创建列表控件
        list_widget = QListWidget()
        list_widget.setObjectName("report_history_list")
        layout.addWidget(list_widget)

        # 添加周报到列表
        for report in reports:
            start_date = datetime.datetime.strptime(
                report["start_date"], "%Y-%m-%d"
            ).date()
            end_date = datetime.datetime.strptime(report["end_date"], "%Y-%m-%d").date()
            date_range = f"{start_date} 至 {end_date}"

            item = QListWidgetItem(date_range)
            item.setData(Qt.ItemDataRole.UserRole, report)
            list_widget.addItem(item)

        # 创建预览区域
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setObjectName("report_preview")
        layout.addWidget(preview_text)

        # 连接列表选择信号
        def on_item_selected(item):
            report = item.data(Qt.ItemDataRole.UserRole)
            preview_text.setPlainText(report["report_text"])

        list_widget.currentItemChanged.connect(on_item_selected)

        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # 显示对话框
        dialog.exec()

    def load_user_data(self, user_data):
        """Load user data and update the UI."""
        self.current_user = user_data
        self.clear_progress()

        # 加载最新的周报
        if user_data:
            latest_report = self.progress_tracker.get_weekly_report(user_data["id"])
            if latest_report:
                self.weekly_report_text = latest_report["report_text"]
                if self.weekly_report_text_edit is not None:
                    self.weekly_report_text_edit.setPlainText(
                        latest_report["report_text"]
                    )
                self.report_last_generated = datetime.datetime.strptime(
                    latest_report["created_at"], "%Y-%m-%d %H:%M:%S"
                )

        self.update_progress_display()

    def update_progress_display(self):
        """Update the progress display based on the loaded user data."""
        if self.current_user:
            self.load_progress()
        else:
            self.clear_progress()

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
            if (
                self.achievements_placeholder and self.achievements_placeholder.parent()
            ):  # Check if it's still part of a valid hierarchy
                self.achievements_placeholder.setText("成就徽章将在此处展示。")
                self.achievements_placeholder.show()
                # Find and collapse spacer
                for i in range(self.achievements_layout.count()):
                    item = self.achievements_layout.itemAt(i)
                    if item and item.spacerItem():
                        item.spacerItem().changeSize(
                            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
                        )
                        break
            else:
                logging.warning(
                    "clear_achievements: achievements_placeholder seems invalid or deleted."
                )
                # Optionally recreate placeholder if necessary, though this indicates a deeper issue
                # self.achievements_placeholder = QLabel("成就徽章将在此处展示。")
                # self.achievements_layout.insertWidget(0, self.achievements_placeholder) # Re-add if needed

        except RuntimeError as e:
            # Catch the specific error if the check somehow fails
            logging.error(
                f"RuntimeError in clear_achievements accessing placeholder: {e}"
            )

    def update_charts(self, check_ins):
        """更新统计图表"""
        if not check_ins:
            return

        # 更新饼图
        if self.pie_chart:
            self.pie_chart.removeAllSeries()
            pie_series = QPieSeries()
            category_counts = {}
            for check_in in check_ins:
                category = check_in.get("category", "未分类")
                category_counts[category] = category_counts.get(category, 0) + 1
            if not category_counts:
                self.pie_chart.setTitle("暂无打卡数据")
                return
            colors = [
                "#4CAF50",
                "#2196F3",
                "#FFC107",
                "#F44336",
                "#9C27B0",
                "#00BCD4",
                "#FF9800",
                "#8BC34A",
            ]
            total = sum(category_counts.values())
            for i, (category, count) in enumerate(category_counts.items()):
                percent = count / total * 100
                label = f"{category} ({count}次, {percent:.1f}%)"
                slice = QPieSlice(label, count)
                slice.setColor(QColor(colors[i % len(colors)]))
                slice.setExploded(True)
                slice.setLabelVisible(True)
                slice.setLabelFont(QFont("Hiragino Sans GB", 13, QFont.Weight.Bold))
                slice.setLabelColor(QColor("#E6E6E6"))
                slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
                pie_series.append(slice)
            self.pie_chart.addSeries(pie_series)
            self.pie_chart.setTitleFont(
                QFont("Hiragino Sans GB", 18, QFont.Weight.Bold)
            )
            self.pie_chart.setTitleBrush(QBrush(QColor("#E6E6E6")))
            self.pie_chart.setBackgroundVisible(False)
            self.pie_chart.legend().setVisible(True)
            self.pie_chart.legend().setFont(
                QFont("Hiragino Sans GB", 15, QFont.Weight.Bold)
            )
            self.pie_chart.legend().setColor(QColor("#E6E6E6"))
            self.pie_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
            self.pie_chart.setMargins(QMargins(40, 40, 40, 40))


class WeeklyReportWidget(QWidget):
    def __init__(self, progress_tracker):
        super().__init__()
        self.progress_tracker = progress_tracker
        self.setup_ui()

    def setup_ui(self):
        """设置周报显示界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("AI周报分析")
        title_font = QFont("Hiragino Sans GB", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        main_layout.addWidget(separator)

        # 周报内容区域
        report_group = QGroupBox("本周总结")
        report_layout = QVBoxLayout()
        report_layout.setSpacing(15)

        # 时间范围
        date_range = QLabel()
        date_range.setObjectName("date_range")
        report_layout.addWidget(date_range)

        # 主要成就
        achievements_group = QGroupBox("主要成就")
        achievements_layout = QVBoxLayout()
        self.achievements_text = QTextEdit()
        self.achievements_text.setReadOnly(True)
        self.achievements_text.setObjectName("report_text")
        achievements_layout.addWidget(self.achievements_text)
        achievements_group.setLayout(achievements_layout)
        report_layout.addWidget(achievements_group)

        # 进步分析
        progress_group = QGroupBox("进步分析")
        progress_layout = QVBoxLayout()
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setObjectName("report_text")
        progress_layout.addWidget(self.progress_text)
        progress_group.setLayout(progress_layout)
        report_layout.addWidget(progress_group)

        # 建议
        suggestions_group = QGroupBox("改进建议")
        suggestions_layout = QVBoxLayout()
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        self.suggestions_text.setObjectName("report_text")
        suggestions_layout.addWidget(self.suggestions_text)
        suggestions_group.setLayout(suggestions_layout)
        report_layout.addWidget(suggestions_group)

        report_group.setLayout(report_layout)
        main_layout.addWidget(report_group)

        # 加载周报数据
        self.load_weekly_report()

    def load_weekly_report(self):
        """加载周报数据"""
        report = self.progress_tracker.get_weekly_report()
        if not report:
            return

        # 更新时间范围
        start_date = report.get("start_date", "")
        end_date = report.get("end_date", "")
        label_range = self.findChild(QLabel, "date_range")
        if label_range is not None:
            label_range.setText(f"报告时间：{start_date} 至 {end_date}")

        # 更新主要成就
        achievements = report.get("achievements", [])
        achievements_text = "\n".join(
            [f"• {achievement}" for achievement in achievements]
        )
        self.achievements_text.setText(achievements_text)

        # 更新进步分析
        progress = report.get("progress", "")
        self.progress_text.setText(progress)

        # 更新建议
        suggestions = report.get("suggestions", [])
        suggestions_text = "\n".join([f"• {suggestion}" for suggestion in suggestions])
        self.suggestions_text.setText(suggestions_text)


# ... (rest of the class) ...
