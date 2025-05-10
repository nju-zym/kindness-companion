from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QTimeEdit,
    QComboBox,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSizePolicy,
    QRadioButton,
    QButtonGroup,
    QTextEdit,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, Slot, QTime, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
import datetime

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox


class ReminderWidget(QWidget):
    """
    Widget for managing reminders and application settings.
    """

    # 添加主题变更信号
    theme_changed = Signal(
        str, str
    )  # 主题类型（light/dark）, 主题样式（standard/warm）

    def __init__(self, reminder_scheduler, challenge_manager, theme_manager=None):
        """
        Initialize the reminder widget.

        Args:
            reminder_scheduler: Reminder scheduler instance
            challenge_manager: Challenge manager instance
            theme_manager: Theme manager instance (optional)
        """
        super().__init__()

        self.reminder_scheduler = reminder_scheduler
        self.challenge_manager = challenge_manager
        self.theme_manager = theme_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            25, 25, 25, 25
        )  # Increased margins for better spacing

        # Header
        self.title_label = QLabel("设置")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.title_label.setProperty("class", "page_title")  # Add class for styling
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("管理应用设置和提醒")
        self.subtitle_label.setObjectName(
            "subtitle_label"
        )  # Set object name for styling
        self.main_layout.addWidget(self.subtitle_label)

        self.main_layout.addSpacing(20)  # Increased spacing for better separation

        # Content layout with scroll area for better handling of content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # Remove frame border

        # Container widget for scroll area
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setSpacing(25)  # Increased spacing between sections
        self.content_layout.setContentsMargins(5, 5, 5, 5)  # Small content margins

        # Create reminder form (Challenge, Time, Create Button)
        self.setup_reminder_form()
        self.content_layout.addWidget(self.reminder_form_group)

        # Add Days Group Box directly to the content layout AFTER the form group
        # self.days_group is created in setup_reminder_form
        self.content_layout.addWidget(self.days_group)

        # Reminder list
        self.setup_reminder_list()
        self.content_layout.addWidget(self.reminder_list_group, 1)  # 增加stretch

        # Set the scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)

        # Add stretch at the end to push content upwards if space allows
        self.content_layout.addStretch()

    def setup_reminder_form(self):
        """优化提醒创建表单布局，使其更美观、紧凑、主操作突出。"""
        self.reminder_form_group = QGroupBox("创建新提醒")
        self.reminder_form_group.setObjectName("reminder_form_group")

        # 使用垂直布局整体包裹
        form_vlayout = QVBoxLayout(self.reminder_form_group)
        form_vlayout.setContentsMargins(25, 25, 25, 20)
        form_vlayout.setSpacing(18)

        # 挑战与时间横向排列
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        challenge_label = QLabel("挑战:")
        challenge_label.setFixedWidth(48)
        self.challenge_combo = QComboBox()
        self.challenge_combo.setMinimumWidth(180)
        row1.addWidget(challenge_label)
        row1.addWidget(self.challenge_combo)
        row1.addSpacing(30)
        time_label = QLabel("时间:")
        time_label.setFixedWidth(40)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))
        self.time_edit.setMinimumWidth(90)
        row1.addWidget(time_label)
        row1.addWidget(self.time_edit)
        row1.addStretch()
        form_vlayout.addLayout(row1)

        # 日期选择（两行排列）
        days_group = QGroupBox("提醒日期")
        days_layout = QGridLayout(days_group)
        days_layout.setContentsMargins(10, 10, 10, 10)
        days_layout.setHorizontalSpacing(18)
        days_layout.setVerticalSpacing(8)
        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)
            self.day_checkboxes.append(checkbox)
            # 两行排列
            row, col = divmod(i, 4)
            days_layout.addWidget(checkbox, row, col)
        form_vlayout.addWidget(days_group)

        # 创建按钮（居中且宽度与输入框一致）
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.create_button = QPushButton("创建提醒")
        self.create_button.setMinimumWidth(160)
        self.create_button.setMinimumHeight(36)
        self.create_button.setObjectName("add_button")
        self.create_button.setIcon(QIcon(":/icons/plus.svg"))
        self.create_button.setIconSize(QSize(16, 16))
        self.create_button.clicked.connect(self.create_reminder)
        btn_layout.addWidget(self.create_button)
        btn_layout.addStretch()
        form_vlayout.addLayout(btn_layout)
        self.days_group = days_group

    def setup_reminder_list(self):
        """Set up the reminder list."""
        self.reminder_list_group = QGroupBox("当前提醒")
        self.reminder_list_group.setObjectName("reminder_list_group")
        self.reminder_list_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.reminder_list_group.setMinimumHeight(360)

        list_layout = QVBoxLayout(self.reminder_list_group)
        list_layout.setContentsMargins(15, 25, 15, 15)  # 增加边距
        list_layout.setSpacing(15)  # 增加间距

        # 提醒表格
        self.reminder_table = QTableWidget()
        self.reminder_table.setObjectName("reminder_table")
        self.reminder_table.setColumnCount(5)
        self.reminder_table.setMinimumHeight(300)
        self.reminder_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.reminder_table.setHorizontalHeaderLabels(
            ["挑战", "时间", "日期", "状态", "操作"]
        )

        # 设置表头样式
        header = self.reminder_table.horizontalHeader()
        header.setObjectName("reminder_table_header")
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # 设置列宽比例
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )  # 挑战列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 时间列固定宽度
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )  # 日期列自适应宽度
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 状态列固定宽度
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 操作列固定宽度

        # 设置固定列的宽度
        self.reminder_table.setColumnWidth(1, 80)  # 时间列宽度
        self.reminder_table.setColumnWidth(3, 80)  # 状态列宽度
        self.reminder_table.setColumnWidth(4, 100)  # 操作列宽度

        # 其他表格设置
        self.reminder_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )  # 不可编辑
        self.reminder_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )  # 选择整行
        self.reminder_table.setAlternatingRowColors(True)  # 交替行颜色
        self.reminder_table.setShowGrid(True)  # 显示网格线
        self.reminder_table.setGridStyle(Qt.PenStyle.SolidLine)  # 实线网格

        # 设置行高
        self.reminder_table.verticalHeader().setDefaultSectionSize(40)  # 设置默认行高
        self.reminder_table.verticalHeader().setVisible(False)  # 隐藏垂直表头

        list_layout.addWidget(self.reminder_table)

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

            # Load reminders
            self.load_reminders()
        else:
            # Clear reminders
            self.clear_reminders()

    def load_user_challenges(self):
        """Load user's subscribed challenges."""
        if not self.current_user:
            return

        # Get user's subscribed challenges
        challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])

        # Clear and repopulate challenge combo
        self.challenge_combo.clear()

        for challenge in challenges:
            self.challenge_combo.addItem(challenge["title"], challenge["id"])

    def load_reminders(self):
        """Load and display reminders."""
        if not self.current_user:
            return

        print(f"Loading reminders for user ID: {self.current_user['id']}")

        # Get user's reminders
        reminders = self.reminder_scheduler.get_user_reminders(self.current_user["id"])
        print(f"Found {len(reminders)} reminders")

        # Clear table completely
        self.reminder_table.clearContents()
        self.reminder_table.setRowCount(0)
        print("Cleared reminder table")

        # Add reminders to table
        for i, reminder in enumerate(reminders):
            print(f"Adding reminder to table: {reminder}")
            self.reminder_table.insertRow(i)

            # Challenge
            challenge_item = QTableWidgetItem(reminder["challenge_title"])
            self.reminder_table.setItem(i, 0, challenge_item)

            # Time
            time_item = QTableWidgetItem(reminder["time"])
            self.reminder_table.setItem(i, 1, time_item)

            # Days
            days = [int(d) for d in reminder["days"].split(",")]
            day_names = self.get_day_names(days)
            days_item = QTableWidgetItem(", ".join(day_names))
            self.reminder_table.setItem(i, 2, days_item)

            # Status
            status_checkbox = QCheckBox()
            status_checkbox.setChecked(reminder["enabled"] == 1)
            status_checkbox.stateChanged.connect(
                lambda state, r=reminder: self.toggle_reminder(r["id"], state)
            )
            self.reminder_table.setCellWidget(i, 3, status_checkbox)

            # 操作按钮
            delete_button = QPushButton("删除")
            delete_button.setObjectName("delete_button")  # 设置对象名称以便样式化
            delete_button.setIcon(QIcon(":/icons/trash-2.svg"))
            delete_button.setIconSize(QSize(16, 16))
            delete_button.setMinimumHeight(32)  # 增加按钮高度

            reminder_id = reminder["id"]
            delete_button.clicked.connect(
                lambda _, rid=reminder_id: self.delete_reminder(rid)
            )

            self.reminder_table.setCellWidget(i, 4, delete_button)

        print("Reminder table population complete")

    def clear_reminders(self):
        """Clear reminders display."""
        # Clear challenge combo
        self.challenge_combo.clear()

        # Clear table
        self.reminder_table.setRowCount(0)

    def create_reminder(self):
        """Create a new reminder."""
        if not self.current_user:
            return

        # Get selected challenge
        if self.challenge_combo.count() == 0:
            AnimatedMessageBox.showWarning(
                self.window(), "创建失败", "您还没有订阅任何挑战，请先订阅挑战。"
            )
            return

        challenge_id = self.challenge_combo.currentData()

        # Get selected time
        time = self.time_edit.time()
        time_str = f"{time.hour():02d}:{time.minute():02d}"

        # Get selected days
        days = []
        for i, checkbox in enumerate(self.day_checkboxes):
            if checkbox.isChecked():
                days.append(i)

        if not days:
            AnimatedMessageBox.showWarning(
                self.window(), "创建失败", "请至少选择一天进行提醒。"
            )
            return

        # Create reminder
        reminder_id = self.reminder_scheduler.create_reminder(
            self.current_user["id"], challenge_id, time_str, days
        )

        if reminder_id:
            # Show success message non-modally using AnimatedMessageBox
            challenge_title = self.challenge_combo.currentText()
            day_names = self.get_day_names(days)

            create_success_msg = AnimatedMessageBox(
                self.window()
            )  # Use AnimatedMessageBox
            create_success_msg.setWindowTitle("创建成功")
            create_success_msg.setText(
                f"已成功创建{challenge_title}的提醒。\n提醒时间: {time_str}\n提醒日期: {', '.join(day_names)}"
            )
            create_success_msg.setIcon(QMessageBox.Icon.Information)
            create_success_msg.showNonModal()  # Use custom non-modal method

            # Reload reminders
            self.load_reminders()
        else:
            # Failure warning using AnimatedMessageBox
            AnimatedMessageBox.showWarning(
                self.window(), "创建失败", "创建提醒失败，请稍后重试。"
            )

    def toggle_reminder(self, reminder_id, state):
        """
        Toggle a reminder's enabled state.

        Args:
            reminder_id (int): Reminder ID
            state (int): Checkbox state
        """
        if not self.current_user:
            return

        enabled = state == Qt.CheckState.Checked

        success = self.reminder_scheduler.update_reminder(reminder_id, enabled=enabled)

        if not success:
            AnimatedMessageBox.showWarning(
                self.window(), "更新失败", "更新提醒状态失败，请稍后重试。"
            )

            # Reload reminders to reset UI
            self.load_reminders()

    def delete_reminder(self, reminder_id):
        """
        Delete a reminder.

        Args:
            reminder_id (int): Reminder ID
        """
        if not self.current_user:
            return

        # Ask for confirmation using AnimatedMessageBox
        reply = QMessageBox.question(
            self.window(),
            "删除提醒",
            "确定要删除这个提醒吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print(f"User confirmed deletion of reminder ID: {reminder_id}")

            # Get reminder info before deletion for debugging
            reminder_info = self.reminder_scheduler.get_user_reminders(
                self.current_user["id"]
            )
            reminder_to_delete = None
            for reminder in reminder_info:
                if reminder["id"] == reminder_id:
                    reminder_to_delete = reminder
                    break

            if reminder_to_delete:
                print(f"Found reminder to delete: {reminder_to_delete}")
            else:
                print(
                    f"Warning: Reminder ID {reminder_id} not found in user's reminders"
                )

            # Attempt to delete the reminder
            print(f"Calling reminder_scheduler.delete_reminder({reminder_id})")
            success = self.reminder_scheduler.delete_reminder(reminder_id)
            print(f"Delete operation returned: {success}")

            # Force reload reminders regardless of success
            print("Reloading reminders list")
            self.load_reminders()

            if success:
                # Show success message
                AnimatedMessageBox.showInformation(
                    self.window(), "删除成功", f"已成功删除提醒。"
                )
            else:
                # Show detailed error message with debugging info
                error_message = "删除提醒失败，请稍后重试。"
                if reminder_to_delete:
                    error_message += f"\n\n调试信息：\n提醒ID: {reminder_id}\n挑战: {reminder_to_delete['challenge_title']}"

                AnimatedMessageBox.showWarning(self.window(), "删除失败", error_message)

    def get_day_names(self, day_numbers):
        """
        Get the names of days of the week.

        Args:
            day_numbers (list): List of day numbers (0-6, where 0 is Monday)

        Returns:
            list: List of day names
        """
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return [days[day % 7] for day in day_numbers]


class ReminderSettingsWidget(QWidget):
    def __init__(self, reminder_manager):
        super().__init__()
        self.reminder_manager = reminder_manager
        self.setup_ui()

    def setup_ui(self):
        """设置提醒设置界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("提醒设置")
        title_font = QFont("Hiragino Sans GB", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        main_layout.addWidget(separator)

        # 提醒时间设置
        time_group = QGroupBox("提醒时间")
        time_layout = QGridLayout()
        time_layout.setSpacing(15)

        # 每日提醒时间
        daily_time_label = QLabel("每日提醒时间:")
        self.daily_time_edit = QTimeEdit()
        self.daily_time_edit.setDisplayFormat("HH:mm")
        self.daily_time_edit.setTime(QTime(9, 0))  # 默认9:00
        time_layout.addWidget(daily_time_label, 0, 0)
        time_layout.addWidget(self.daily_time_edit, 0, 1)

        # 提醒频率
        frequency_label = QLabel("提醒频率:")
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["每天", "工作日", "周末", "自定义"])
        time_layout.addWidget(frequency_label, 1, 0)
        time_layout.addWidget(self.frequency_combo, 1, 1)

        # 自定义提醒时间
        custom_time_label = QLabel("自定义提醒时间:")
        self.custom_time_edit = QTimeEdit()
        self.custom_time_edit.setDisplayFormat("HH:mm")
        self.custom_time_edit.setTime(QTime(20, 0))  # 默认20:00
        time_layout.addWidget(custom_time_label, 2, 0)
        time_layout.addWidget(self.custom_time_edit, 2, 1)

        time_group.setLayout(time_layout)
        main_layout.addWidget(time_group)

        # 提醒方式设置
        method_group = QGroupBox("提醒方式")
        method_layout = QVBoxLayout()
        method_layout.setSpacing(10)

        # 提醒方式选项
        self.desktop_notify = QCheckBox("桌面通知")
        self.desktop_notify.setChecked(True)
        self.email_notify = QCheckBox("邮件提醒")
        self.sms_notify = QCheckBox("短信提醒")

        method_layout.addWidget(self.desktop_notify)
        method_layout.addWidget(self.email_notify)
        method_layout.addWidget(self.sms_notify)

        method_group.setLayout(method_layout)
        main_layout.addWidget(method_group)

        # 提醒内容设置
        content_group = QGroupBox("提醒内容")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)

        # 提醒消息模板
        template_label = QLabel("提醒消息模板:")
        self.template_edit = QTextEdit()
        self.template_edit.setPlaceholderText(
            "输入提醒消息模板，可使用 {challenge_name} 等变量"
        )
        self.template_edit.setMaximumHeight(100)

        content_layout.addWidget(template_label)
        content_layout.addWidget(self.template_edit)

        content_group.setLayout(content_layout)
        main_layout.addWidget(content_group)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        save_button = QPushButton("保存设置")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.save_settings)

        test_button = QPushButton("测试提醒")
        test_button.clicked.connect(self.test_reminder)

        button_layout.addStretch()
        button_layout.addWidget(test_button)
        button_layout.addWidget(save_button)

        main_layout.addLayout(button_layout)

        # 加载当前设置
        self.load_settings()

    def load_settings(self):
        """加载当前提醒设置"""
        settings = self.reminder_manager.get_reminder_settings()
        if settings:
            self.daily_time_edit.setTime(
                QTime.fromString(settings.get("daily_time", "09:00"), "HH:mm")
            )
            self.frequency_combo.setCurrentText(settings.get("frequency", "每天"))
            self.custom_time_edit.setTime(
                QTime.fromString(settings.get("custom_time", "20:00"), "HH:mm")
            )
            self.desktop_notify.setChecked(settings.get("desktop_notify", True))
            self.email_notify.setChecked(settings.get("email_notify", False))
            self.sms_notify.setChecked(settings.get("sms_notify", False))
            self.template_edit.setText(settings.get("template", ""))

    def save_settings(self):
        """保存提醒设置"""
        settings = {
            "daily_time": self.daily_time_edit.time().toString("HH:mm"),
            "frequency": self.frequency_combo.currentText(),
            "custom_time": self.custom_time_edit.time().toString("HH:mm"),
            "desktop_notify": self.desktop_notify.isChecked(),
            "email_notify": self.email_notify.isChecked(),
            "sms_notify": self.sms_notify.isChecked(),
            "template": self.template_edit.toPlainText(),
        }

        if self.reminder_manager.update_reminder_settings(settings):
            QMessageBox.information(self.window(), "成功", "提醒设置已保存")
        else:
            QMessageBox.warning(self.window(), "错误", "保存设置失败")

    def test_reminder(self):
        """测试提醒功能"""
        if self.reminder_manager.send_test_reminder():
            QMessageBox.information(self.window(), "成功", "测试提醒已发送")
        else:
            QMessageBox.warning(self.window(), "错误", "发送测试提醒失败")
