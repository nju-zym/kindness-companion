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
    QTableView,
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
                # 提取用户ID作为参数，兼容新的API
                if (
                    isinstance(self.report_input, dict)
                    and "user_id" in self.report_input
                ):
                    user_id = self.report_input["user_id"]
                    result = self.generator_func(user_id, 7)  # 默认7天的报告

                    # 处理返回结果
                    if isinstance(result, dict):
                        if result.get("success", False):
                            # 生成成功，格式化报告内容
                            report_text = self.format_report_text(result)
                            self.report_ready.emit(report_text)
                        else:
                            # 生成失败，显示错误信息
                            error_msg = result.get("message", "报告生成失败")
                            self.report_error.emit(error_msg)
                    else:
                        # 处理字符串返回值（向后兼容）
                        self.report_ready.emit(str(result))
                else:
                    # 兼容旧的调用方式
                    report = self.generator_func(self.report_input)
                    self.report_ready.emit(str(report))
            else:
                self.report_error.emit("报告生成功能不可用")
        except Exception as e:
            logging.error(f"Error in AI report thread: {e}", exc_info=True)
            self.report_error.emit(f"生成报告时出错: {e}")

    def format_report_text(self, result: dict) -> str:
        """将API结果格式化为可读的报告文本"""
        try:
            report_lines = []
            report_lines.append("=== 心理健康周报 ===\n")

            # 报告时间段
            period = result.get("report_period", "过去7天")
            report_lines.append(f"📅 报告时间段: {period}\n")

            # PERMA得分
            perma_scores = result.get("perma_scores", {})
            if perma_scores:
                report_lines.append("📊 PERMA幸福感得分:")
                report_lines.append(
                    f"  • 积极情感: {perma_scores.get('positive_emotion', 0):.1f}/10"
                )
                report_lines.append(
                    f"  • 投入感: {perma_scores.get('engagement', 0):.1f}/10"
                )
                report_lines.append(
                    f"  • 人际关系: {perma_scores.get('relationships', 0):.1f}/10"
                )
                report_lines.append(
                    f"  • 人生意义: {perma_scores.get('meaning', 0):.1f}/10"
                )
                report_lines.append(
                    f"  • 成就感: {perma_scores.get('achievement', 0):.1f}/10"
                )
                report_lines.append(
                    f"  • 整体幸福感: {perma_scores.get('overall_wellbeing', 0):.1f}/10\n"
                )

            # 心理学洞察
            insights = result.get("insights", [])
            if insights:
                report_lines.append("🔍 心理学洞察:")
                for insight in insights[:3]:  # 最多显示3个洞察
                    category = insight.get("category", "")
                    content = insight.get("content", "")
                    confidence = insight.get("confidence", 0)
                    report_lines.append(
                        f"  • {category}: {content} (置信度: {confidence:.2f})"
                    )
                report_lines.append("")

            # 成长建议
            recommendations = result.get("recommendations", [])
            if recommendations:
                report_lines.append("💡 成长建议:")
                for i, rec in enumerate(recommendations[:5], 1):  # 最多显示5个建议
                    report_lines.append(f"  {i}. {rec}")
                report_lines.append("")

            # 保护因素和风险因素
            protective_factors = result.get("protective_factors", [])
            risk_factors = result.get("risk_factors", [])

            if protective_factors:
                report_lines.append("✅ 保护因素:")
                for factor in protective_factors[:3]:
                    report_lines.append(f"  • {factor}")
                report_lines.append("")

            if risk_factors:
                report_lines.append("⚠️ 需要关注:")
                for factor in risk_factors[:3]:
                    report_lines.append(f"  • {factor}")
                report_lines.append("")

            # 报告置信度
            confidence = result.get("confidence", 0)
            report_lines.append(f"📈 分析置信度: {confidence:.2f}/1.0")

            # 生成时间
            generated_at = result.get("generated_at", "")
            if generated_at:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                    report_lines.append(
                        f"🕐 生成时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                except:
                    report_lines.append(f"🕐 生成时间: {generated_at}")

            return "\n".join(report_lines)

        except Exception as e:
            logging.error(f"格式化报告文本失败: {e}")
            return f"报告生成成功，但格式化失败: {str(result)}"


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

        # Initialize UI attributes to None for clarity
        self.main_layout = None
        self.title_label = None
        self.challenge_label = None
        self.challenge_combo = None
        self.range_label = None
        self.range_combo = None
        self.calendar_widget = None
        self.total_label = None
        self.streak_label = None
        self.rate_label = None
        self.weekly_report_text_edit = None
        self.generate_report_button = None
        self.history_button = None
        self.report_progress_bar = None
        self.achievements_scroll_area = None
        self.achievements_container = None
        self.achievements_layout = None
        self.achievements_placeholder = None
        self.achievements_spacer = None
        self.progress_table = None

        # New tab-based layout attributes
        self.tab_widget = None
        self.overview_tab = None
        self.details_tab = None
        self.analysis_tab = None
        self.pie_chart = None
        self.pie_view = None

        self.setup_ui()

    def setup_ui(self):
        """重构打卡记录界面布局，优化小窗口显示和饼图布局。"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            2, 2, 2, 2
        )  # 最大化减少边距为日历腾出最多空间
        self.main_layout.setSpacing(4)  # 最大化减少间距为日历腾出最多空间

        # 移除过度严格的尺寸约束
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # 顶部标题与筛选器
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.title_label = QLabel("打卡记录")
        self.title_label.setObjectName("title_label")
        self.title_label.setFont(QFont("Hiragino Sans GB", 20, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # 筛选器组
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        self.challenge_label = QLabel("挑战:")
        self.challenge_combo = QComboBox()
        self.challenge_combo.setMinimumWidth(140)
        self.challenge_combo.setMaximumWidth(200)
        self.challenge_combo.addItem("全部挑战", None)
        self.challenge_combo.currentIndexChanged.connect(self.load_progress)

        self.range_label = QLabel("时间:")
        self.range_combo = QComboBox()
        self.range_combo.setMinimumWidth(100)
        self.range_combo.setMaximumWidth(150)
        self.range_combo.addItem("最近7天", 7)
        self.range_combo.addItem("最近30天", 30)
        self.range_combo.addItem("最近90天", 90)
        self.range_combo.addItem("全部记录", None)
        self.range_combo.currentIndexChanged.connect(self.load_progress)

        filter_layout.addWidget(self.challenge_label)
        filter_layout.addWidget(self.challenge_combo)
        filter_layout.addWidget(self.range_label)
        filter_layout.addWidget(self.range_combo)

        header_layout.addWidget(filter_widget)
        self.main_layout.addLayout(header_layout)

        # 使用TabWidget来节省空间并改善组织
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("progress_tab_widget")

        # 概览标签页 - 包含日历、统计和图表
        self.overview_tab = QWidget()
        self.setup_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 概览")

        # 详细记录标签页 - 包含表格
        self.details_tab = QWidget()
        self.setup_details_tab()
        self.tab_widget.addTab(self.details_tab, "📋 详细记录")

        # AI分析标签页 - 包含AI周报和成就
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "🤖 AI分析")

        # 连接Tab切换事件
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.main_layout.addWidget(self.tab_widget)

    def setup_overview_tab(self):
        """设置概览标签页"""
        layout = QVBoxLayout(self.overview_tab)
        layout.setContentsMargins(2, 2, 2, 2)  # 最大化减少内边距为日历腾出最多空间
        layout.setSpacing(6)  # 最大化减少间距为日历腾出最多空间

        # 上半部分：日历和基础统计
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)  # 最大化减少间距为日历腾出最多空间

        # 日历部分
        calendar_group = QGroupBox("日历视图")
        calendar_group.setObjectName("calendar_group")
        calendar_layout = QVBoxLayout(calendar_group)
        calendar_layout.setContentsMargins(
            1, 1, 1, 1
        )  # 最大化减少内边距，为日历腾出最多空间

        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setObjectName("calendar_widget")
        # 设置更大的高度，确保有足够空间显示日历内容
        self.calendar_widget.setMaximumHeight(
            320
        )  # 进一步增加到320px给日历最充足的显示空间
        self.calendar_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.calendar_widget.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar_widget.setSelectionMode(
            QCalendarWidget.SelectionMode.SingleSelection
        )

        # 配置日历样式，隐藏相邻月份的日期
        self.setup_calendar_style()

        self.calendar_widget.clicked.connect(self.calendar_date_clicked)
        calendar_layout.addWidget(self.calendar_widget)

        # 基础统计信息
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(8)

        self.total_label = QLabel("总打卡次数: 0")
        self.total_label.setObjectName("stat_label")
        self.streak_label = QLabel("当前连续打卡: 0 天")
        self.streak_label.setObjectName("stat_label")
        self.rate_label = QLabel("完成率: 0%")
        self.rate_label.setObjectName("stat_label")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.streak_label)
        stats_layout.addWidget(self.rate_label)
        stats_layout.addStretch()

        top_layout.addWidget(calendar_group, 2)
        top_layout.addWidget(stats_widget, 1)

        layout.addLayout(top_layout)

        # 下半部分：饼图
        chart_group = QGroupBox("类别分布")
        chart_group.setObjectName("chart_group")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(
            3, 5, 3, 3  # 减少上边距，把空间留给内部元素控制
        )  # 进一步减少内边距为日历腾出更多空间

        # 添加一个空白空间确保顶部标签有显示空间
        top_spacer = QSpacerItem(
            20,
            40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,  # 固定40px高度的顶部留白
        )
        chart_layout.addSpacerItem(top_spacer)

        # 优化饼图设置
        self.pie_chart = QChart()
        # 移除图表内部的标题，只使用GroupBox的标题来节省空间
        # self.pie_chart.setTitle("挑战类别分布")  # 注释掉内部标题
        self.pie_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.pie_chart.legend().setVisible(True)
        self.pie_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        # 设置主题适配的标题颜色
        app = QApplication.instance()
        theme = "light"
        if app:
            theme_manager = app.property("theme_manager")
            if theme_manager:
                theme = theme_manager.current_theme
        if theme == "light":
            self.pie_chart.setTitleBrush(QBrush(QColor("#333333")))
        else:
            self.pie_chart.setTitleBrush(QBrush(QColor("#E6E6E6")))

        self.pie_view = QChartView(self.pie_chart)
        self.pie_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.pie_view.setMinimumHeight(
            380  # 减少高度，为上方留白腾出空间
        )  # 增加最小高度，配合增加的上边距给上方标签更多空间
        self.pie_view.setMaximumHeight(480)  # 相应减少最大高度
        self.pie_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # 设置图表视图的渲染提示以获得更好的文字显示效果
        self.pie_view.setRubberBand(QChartView.RubberBand.NoRubberBand)

        chart_layout.addWidget(self.pie_view)
        layout.addWidget(chart_group)

    def setup_details_tab(self):
        """设置详细记录标签页"""
        layout = QVBoxLayout(self.details_tab)
        layout.setContentsMargins(2, 2, 2, 2)  # 最大化减少内边距为日历腾出最多空间
        layout.setSpacing(4)  # 最大化减少间距为日历腾出最多空间

        # 表格
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
        self.progress_table.verticalHeader().setDefaultSectionSize(40)
        self.progress_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.progress_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.progress_table.setAlternatingRowColors(True)
        self.progress_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.progress_table)

    def setup_analysis_tab(self):
        """设置AI分析标签页"""
        layout = QVBoxLayout(self.analysis_tab)
        layout.setContentsMargins(2, 2, 2, 2)  # 最大化减少内边距为日历腾出最多空间
        layout.setSpacing(4)  # 最大化减少间距为日历腾出最多空间

        # AI周报部分
        ai_group = QGroupBox("AI 周报")
        ai_group.setObjectName("weekly_report_group")
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setContentsMargins(3, 3, 3, 3)  # 进一步减少内边距为日历腾出更多空间
        ai_layout.setSpacing(6)  # 进一步减少间距为日历腾出更多空间

        self.weekly_report_text_edit = QTextEdit()
        self.weekly_report_text_edit.setReadOnly(True)
        self.weekly_report_text_edit.setPlaceholderText(
            "点击下方按钮生成本周善行报告..."
        )
        self.weekly_report_text_edit.setMinimumHeight(120)
        self.weekly_report_text_edit.setMaximumHeight(200)
        ai_layout.addWidget(self.weekly_report_text_edit)

        self.report_progress_bar = QProgressBar()
        self.report_progress_bar.setVisible(False)
        self.report_progress_bar.setRange(0, 0)
        self.report_progress_bar.setTextVisible(False)
        ai_layout.addWidget(self.report_progress_bar)

        # 按钮布局
        ai_btn_layout = QHBoxLayout()
        ai_btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.generate_report_button = QPushButton("生成周报")
        self.generate_report_button.setObjectName("generate_report_button")
        self.generate_report_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.generate_report_button.setFixedSize(110, 32)
        self.generate_report_button.clicked.connect(self.generate_weekly_report)

        self.history_button = QPushButton("历史记录")
        self.history_button.setObjectName("history_button")
        self.history_button.setIcon(QIcon(":/icons/history.svg"))
        self.history_button.setFixedSize(110, 32)
        self.history_button.clicked.connect(self.show_report_history)

        ai_btn_layout.addWidget(self.generate_report_button)
        ai_btn_layout.addWidget(self.history_button)
        ai_layout.addLayout(ai_btn_layout)

        layout.addWidget(ai_group)

        # 成就部分
        achievements_group = QGroupBox("我的成就")
        achievements_group.setObjectName("achievements_group")
        achievements_layout = QVBoxLayout(achievements_group)
        achievements_layout.setContentsMargins(
            2, 2, 2, 2
        )  # 减少内边距为日历腾出更多空间
        achievements_layout.setSpacing(6)  # 减少间距为日历腾出更多空间

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
        self.achievements_layout.setSpacing(6)  # 减少间距为日历腾出更多空间
        self.achievements_layout.setContentsMargins(
            2, 2, 2, 2
        )  # 减少内边距为日历腾出更多空间

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

        layout.addWidget(achievements_group)

    def resizeEvent(self, event):
        """优化响应式布局"""
        width = self.width()
        height = self.height()

        # 根据窗口大小调整字体和间距
        if width < 800 or height < 600:  # 小窗口
            # 调整字体大小
            if hasattr(self, "title_label") and self.title_label:
                self.title_label.setFont(
                    QFont("Hiragino Sans GB", 18, QFont.Weight.Bold)
                )

            # 调整间距
            if hasattr(self, "main_layout") and self.main_layout:
                self.main_layout.setContentsMargins(2, 2, 2, 2)  # 最大化减少小窗口边距
                self.main_layout.setSpacing(4)  # 最大化减少小窗口间距

            # 调整饼图高度 - 由于有了顶部留白，减少图表本身高度
            if hasattr(self, "pie_view") and self.pie_view:
                self.pie_view.setMinimumHeight(320)  # 小窗口时减少高度
                self.pie_view.setMaximumHeight(400)

            # 调整日历高度
            if hasattr(self, "calendar_widget") and self.calendar_widget:
                self.calendar_widget.setMaximumHeight(220)  # 小窗口时也给更多空间

        else:  # 大窗口
            # 恢复正常字体大小
            if hasattr(self, "title_label") and self.title_label:
                self.title_label.setFont(
                    QFont("Hiragino Sans GB", 20, QFont.Weight.Bold)
                )

            # 恢复正常间距
            if hasattr(self, "main_layout") and self.main_layout:
                self.main_layout.setContentsMargins(6, 6, 6, 6)  # 进一步优化大窗口边距
                self.main_layout.setSpacing(6)  # 进一步优化大窗口间距

            # 恢复饼图高度 - 由于有了顶部留白，使用适中的高度
            if hasattr(self, "pie_view") and self.pie_view:
                self.pie_view.setMinimumHeight(380)  # 大窗口时使用适中高度
                self.pie_view.setMaximumHeight(480)

            # 恢复日历高度
            if hasattr(self, "calendar_widget") and self.calendar_widget:
                self.calendar_widget.setMaximumHeight(320)  # 大窗口时使用最大高度

        # 强制刷新图表以适应新的尺寸
        if hasattr(self, "pie_view") and self.pie_view:
            # 使用QTimer延迟刷新，确保布局已经完成
            QTimer.singleShot(100, self.refresh_chart_layout)

        super().resizeEvent(event)

    def refresh_chart_layout(self):
        """刷新图表布局以确保标签正确显示"""
        if self.pie_view and self.current_user:
            # 重新绘制图表
            self.pie_view.update()
            # 如果有数据，重新更新图表
            if hasattr(self, "current_user") and self.current_user:
                # 获取当前的check_ins数据并重新更新图表
                challenge_id = (
                    self.challenge_combo.currentData() if self.challenge_combo else None
                )
                days = self.range_combo.currentData() if self.range_combo else None

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
                else:
                    check_ins = self.progress_tracker.get_all_user_check_ins(
                        self.current_user["id"],
                        start_date.isoformat() if start_date else None,
                        end_date.isoformat(),
                    )

                self.update_charts(check_ins)

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
        # Clear previous formatting for all dates in the current view
        if self.calendar_widget is not None:
            # Get the currently visible month range
            if hasattr(self.calendar_widget, "monthShown"):
                current_month = self.calendar_widget.monthShown()
                current_year = self.calendar_widget.yearShown()
            else:
                current_month = QDate.currentDate().month()
                current_year = QDate.currentDate().year()

            # Clear formatting for the entire visible month
            start_date = QDate(current_year, current_month, 1)
            end_date = start_date.addMonths(1).addDays(-1)

            default_format = QTextCharFormat()
            date_iter = start_date
            while date_iter <= end_date:
                if hasattr(self.calendar_widget, "setDateTextFormat"):
                    self.calendar_widget.setDateTextFormat(date_iter, default_format)
                date_iter = date_iter.addDays(1)

        # Get current theme for color adaptation
        current_theme = self.get_current_theme()

        # Highlight check-in dates with theme-adapted colors
        check_in_format = QTextCharFormat()
        if current_theme == "dark":
            # Dark theme: use lighter background with dark text
            check_in_format.setBackground(QBrush(QColor("#4CAF50")))  # Medium green
            check_in_format.setForeground(QBrush(QColor("#FFFFFF")))  # White text
        else:
            # Light theme: use darker background with light text for better contrast
            check_in_format.setBackground(QBrush(QColor("#2E7D32")))  # Dark green
            check_in_format.setForeground(QBrush(QColor("#FFFFFF")))  # White text

        check_in_dates = {
            QDate.fromString(ci["check_in_date"], "yyyy-MM-dd") for ci in check_ins
        }

        # Apply highlighting to check-in dates
        for date in check_in_dates:
            if date.isValid() and self.calendar_widget is not None:
                if hasattr(self.calendar_widget, "setDateTextFormat"):
                    self.calendar_widget.setDateTextFormat(date, check_in_format)

        # 隐藏相邻月份的日期
        QTimer.singleShot(50, self.update_calendar_display)

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

    def get_current_theme(self):
        """获取当前主题"""
        app = QApplication.instance()
        if app:
            theme_manager = app.property("theme_manager")
            if theme_manager:
                return theme_manager.current_theme
        return "light"  # 默认浅色主题

    def update_charts(self, check_ins):
        """更新统计图表，优化饼图显示，解决文字显示不全问题"""
        if not self.pie_chart:
            return

        # 清空之前的数据
        self.pie_chart.removeAllSeries()

        if not check_ins:
            # 没有数据时不设置标题，保持一致性
            # self.pie_chart.setTitle("暂无打卡数据")
            return

        # 统计各类别数据
        category_counts = {}
        for check_in in check_ins:
            category = check_in.get("category", "未分类")
            category_counts[category] = category_counts.get(category, 0) + 1

        if not category_counts:
            # 没有数据时不设置标题，保持一致性
            # self.pie_chart.setTitle("暂无打卡数据")
            return

        # 创建饼图数据
        pie_series = QPieSeries()
        colors = [
            "#4CAF50",  # 绿色
            "#2196F3",  # 蓝色
            "#FFC107",  # 黄色
            "#FF5722",  # 橙红色
            "#9C27B0",  # 紫色
            "#00BCD4",  # 青色
            "#FF9800",  # 橙色
            "#8BC34A",  # 浅绿色
        ]

        total = sum(category_counts.values())
        current_theme = self.get_current_theme()

        # 按数量排序，显示最大的几个类别
        sorted_categories = sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )

        # 获取图表视图的当前尺寸来动态调整显示策略
        chart_width = self.pie_view.width() if self.pie_view else 400
        chart_height = self.pie_view.height() if self.pie_view else 300

        # 根据图表大小决定显示策略
        is_small_chart = chart_width < 320 or chart_height < 240  # 降低小图表的判断阈值
        max_categories = 4 if is_small_chart else 6

        # 动态调整字体大小
        if is_small_chart:
            label_font_size = 9  # 增加小图表的字体大小
            title_font_size = 12
            legend_font_size = 8
        else:
            label_font_size = 10  # 增加大图表的字体大小
            title_font_size = 14
            legend_font_size = 9

        for i, (category, count) in enumerate(sorted_categories):
            percent = count / total * 100

            # 如果类别太多，合并小的类别
            if i >= max_categories and percent < 8:  # 调整合并阈值
                if "其他" not in [item[0] for item in sorted_categories[:i]]:
                    remaining_count = sum([item[1] for item in sorted_categories[i:]])
                    remaining_percent = remaining_count / total * 100

                    # 简化"其他"类别的标签
                    other_label = (
                        f"其他\n{remaining_percent:.1f}%"
                        if not is_small_chart
                        else "其他"
                    )
                    slice = QPieSlice(other_label, remaining_count)
                    slice.setColor(QColor("#90A4AE"))  # 灰色用于"其他"
                    slice.setLabelVisible(True)  # 确保"其他"类别标签始终可见

                    # 为"其他"类别也应用主题适配的标签颜色
                    if current_theme == "dark":
                        slice.setLabelColor(
                            QColor("#FFFFFF")
                        )  # 使用纯白色确保在深色主题下最大对比度
                    else:
                        slice.setLabelColor(QColor("#000000"))  # 纯黑色，最大对比度

                    slice.setLabelFont(
                        QFont("Hiragino Sans GB", label_font_size, QFont.Weight.Bold)
                    )
                    slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
                    slice.setLabelArmLengthFactor(
                        0.22 if is_small_chart else 0.30
                    )  # 使用统一的臂长度

                    # 设置边框
                    if current_theme == "dark":
                        slice.setBorderColor(QColor("#90A4AE").darker(120))
                    else:
                        slice.setBorderColor(QColor("#2C2C2C"))
                    slice.setBorderWidth(2)

                    pie_series.append(slice)
                break

            # 优化标签文本 - 根据图表大小调整
            if is_small_chart:
                # 小图表：显示简化的类别名，去掉详细统计
                display_category = (
                    category[:3] + "..." if len(category) > 4 else category
                )
                label = f"{display_category}\n{percent:.0f}%"
            else:
                # 大图表：显示完整的类别名和百分比
                display_category = (
                    category[:6] + "..." if len(category) > 8 else category
                )
                label = f"{display_category}\n{percent:.1f}%"

            slice = QPieSlice(label, count)
            slice.setColor(QColor(colors[i % len(colors)]))

            # 只突出显示最大的类别，且调整突出程度
            if i == 0 and len(sorted_categories) > 1:
                slice.setExploded(True)
                slice.setExplodeDistanceFactor(0.05)  # 减小突出距离

            # 设置标签显示 - 确保显示类别信息
            slice.setLabelVisible(True)  # 始终显示标签

            # 根据主题设置标签颜色
            if current_theme == "dark":
                slice.setLabelColor(
                    QColor("#FFFFFF")
                )  # 使用纯白色确保在深色主题下最大对比度
            else:
                slice.setLabelColor(QColor("#000000"))  # 纯黑色，最大对比度

            slice.setLabelFont(
                QFont(
                    "Hiragino Sans GB", label_font_size, QFont.Weight.Bold
                )  # 使用粗体增强可见性
            )
            slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)

            # 调整标签臂长度 - 找到平衡点：避免重叠但不要太长
            slice.setLabelArmLengthFactor(
                0.22 if is_small_chart else 0.30  # 适当增加臂长度，配合增加的空间
            )  # 显著减少臂长度

            # 设置边框以增强标签可见性 - 在浅色主题下使用更深的边框
            if current_theme == "dark":
                slice.setBorderColor(QColor(colors[i % len(colors)]).darker(120))
            else:
                slice.setBorderColor(QColor("#2C2C2C"))  # 浅色主题下使用深色边框
            slice.setBorderWidth(2)  # 增加边框宽度

            # 强制确保标签可见性
            slice.setLabelVisible(True)  # 再次确认标签可见

            pie_series.append(slice)

        # 添加数据到图表
        self.pie_chart.addSeries(pie_series)

        # 手动调整扇形起始角度以优化标签分布
        if pie_series.count() > 0:
            # 设置起始角度，让第一个扇形从12点钟方向开始，确保最大类别在顶部
            pie_series.setPieStartAngle(90)  # 90度表示从12点钟方向开始
            pie_series.setPieEndAngle(450)  # 完整的360度

            # 只对第一个最大的类别设置轻微爆炸效果
            if len(sorted_categories) >= 2:
                slices = pie_series.slices()
                # 强制确保所有标签都可见
                for slice_obj in slices:
                    slice_obj.setLabelVisible(True)  # 强制设置每个切片的标签可见
                    # 确保标签位置在外侧
                    slice_obj.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
                # 只有第一个切片设置爆炸效果，让它更显眼
                if len(slices) > 0:
                    slices[0].setExploded(True)
                    slices[0].setExplodeDistanceFactor(0.05)

        # 优化图表样式
        # 移除标题设置，只使用GroupBox标题
        # title = "类别分布" if is_small_chart else "挑战类别分布"
        # self.pie_chart.setTitle(title)
        # self.pie_chart.setTitleFont(
        #     QFont("Hiragino Sans GB", title_font_size, QFont.Weight.Bold)
        # )

        # 根据主题设置标题颜色（已移除标题，保留注释供参考）
        # if current_theme == "dark":
        #     self.pie_chart.setTitleBrush(QBrush(QColor("#E6E6E6")))
        # else:
        #     self.pie_chart.setTitleBrush(QBrush(QColor("#333333")))

        self.pie_chart.setBackgroundVisible(False)

        # 优化图例设置 - 图例显示完整信息
        legend = self.pie_chart.legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignmentFlag.AlignBottom)
        legend.setFont(QFont("Hiragino Sans GB", legend_font_size, QFont.Weight.Normal))

        if current_theme == "dark":
            legend.setColor(QColor("#E6E6E6"))
        else:
            legend.setColor(QColor("#333333"))

        # 设置合适的图表边距，确保标签和图例有足够空间
        # 由于移除了内部标题，可以减少上边距，为标签留出更多空间
        # 大幅增加上边距，确保最上方的标签能完整显示
        if is_small_chart:
            margins = QMargins(
                25, 50, 25, 40  # 大幅增加上边距到50，确保顶部标签完整显示
            )  # 为饼图上方标签留出足够的显示空间
        else:
            margins = QMargins(
                35, 60, 35, 50  # 大幅增加上边距到60，确保顶部标签完整显示
            )  # 为饼图上方标签留出足够的显示空间

        self.pie_chart.setMargins(margins)

        # 移除隐藏标签的逻辑，确保标签始终可见
        # 由于我们已经为上方预留了足够空间，不再需要隐藏标签
        # if chart_width < 250 or chart_height < 180:  # 进一步降低隐藏标签的阈值
        #     series = self.pie_chart.series()[0]
        #     if hasattr(series, "slices"):
        #         for slice_obj in series.slices():
        #             slice_obj.setLabelVisible(False)
        #         # 在隐藏标签时，确保图例显示更详细的信息
        #         legend.setVisible(True)
        #         legend.setAlignment(
        #             Qt.AlignmentFlag.AlignRight
        #         )  # 改为右侧对齐节省底部空间

    def on_tab_changed(self, index):
        """处理Tab切换事件，刷新相应内容"""
        if index == 0:  # 概览标签页
            # 刷新图表
            if self.current_user:
                self.load_progress()
        elif index == 1:  # 详细记录标签页
            # 表格已经在load_progress中更新，无需额外操作
            pass
        elif index == 2:  # AI分析标签页
            # 刷新成就
            if self.current_user:
                self.load_achievements()

    def setup_calendar_style(self):
        """配置日历样式，隐藏相邻月份的日期"""
        try:
            # 连接月份变化信号来更新显示
            self.calendar_widget.currentPageChanged.connect(
                self.update_calendar_display
            )
            # 初始调用一次来设置当前显示
            QTimer.singleShot(100, self.update_calendar_display)

        except Exception as e:
            print(f"设置日历样式时出错: {e}")

    def update_calendar_display(self):
        """更新日历显示，隐藏相邻月份的日期"""
        try:
            current_date = self.calendar_widget.selectedDate()
            current_month = current_date.month()
            current_year = current_date.year()

            # 设置格式来隐藏相邻月份的日期
            transparent_format = QTextCharFormat()
            transparent_format.setForeground(
                QBrush(QColor(255, 255, 255, 0))
            )  # 完全透明

            normal_format = QTextCharFormat()
            current_theme = self.get_current_theme()
            if current_theme == "dark":
                normal_format.setForeground(QBrush(QColor("#E6E6E6")))
            else:
                normal_format.setForeground(QBrush(QColor("#2D2A26")))

            # 获取当前显示月份的范围
            first_day_of_month = QDate(current_year, current_month, 1)
            last_day_of_month = QDate(
                current_year, current_month, first_day_of_month.daysInMonth()
            )

            # 隐藏当前月份之外的所有日期
            # 遍历整个日历视图的可能日期范围
            start_date = first_day_of_month.addDays(-42)  # 前6周
            end_date = first_day_of_month.addDays(42)  # 后6周

            current_iter = start_date
            while current_iter <= end_date:
                if current_iter.month() != current_month:
                    # 隐藏相邻月份的日期
                    self.calendar_widget.setDateTextFormat(
                        current_iter, transparent_format
                    )
                else:
                    # 确保当前月份的日期可见
                    self.calendar_widget.setDateTextFormat(current_iter, normal_format)
                current_iter = current_iter.addDays(1)

        except Exception as e:
            print(f"更新日历显示时出错: {e}")


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
