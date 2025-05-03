from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTimeEdit, QComboBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QMessageBox, QGroupBox, QFormLayout, QSizePolicy, QRadioButton, QButtonGroup
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
    theme_changed = Signal(str, str)  # 主题类型（light/dark）, 主题样式（standard/warm）

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
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        self.title_label = QLabel("设置")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("管理应用设置和提醒")
        self.main_layout.addWidget(self.subtitle_label)

        self.main_layout.addSpacing(15) # Reduced spacing slightly

        # Content layout (Changed to QVBoxLayout)
        self.content_layout = QVBoxLayout() # Changed from QHBoxLayout to QVBoxLayout
        self.content_layout.setSpacing(20) # Add spacing between form and list

        # 添加主题设置部分
        if self.theme_manager:
            self.setup_theme_settings()
            self.content_layout.addWidget(self.theme_settings_group)
            self.content_layout.addSpacing(10)

        # Create reminder form (Challenge, Time, Create Button)
        self.setup_reminder_form()
        self.content_layout.addWidget(self.reminder_form_group) # Add form group directly

        # Add Days Group Box directly to the content layout AFTER the form group
        # self.days_group is created in setup_reminder_form
        self.content_layout.addWidget(self.days_group)

        # Reminder list
        self.setup_reminder_list()
        self.content_layout.addWidget(self.reminder_list_group) # Add list group directly

        self.main_layout.addLayout(self.content_layout)
        self.main_layout.addStretch() # Add stretch to push content upwards if space allows

    def setup_reminder_form(self):
        """Set up the reminder creation form using QFormLayout.""" # Docstring updated
        self.reminder_form_group = QGroupBox("创建新提醒")
        # Use QFormLayout instead of QVBoxLayout
        form_layout = QFormLayout(self.reminder_form_group) # Changed QVBoxLayout to QFormLayout and renamed variable
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(10, 25, 10, 15) # Keep existing margins
        # Set label alignment for QFormLayout
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Challenge selection
        self.challenge_combo = QComboBox()
        self.challenge_combo.setMinimumWidth(200)
        # Add challenge combo to the form layout
        form_layout.addRow("挑战:", self.challenge_combo) # Use form_layout.addRow

        # Time selection
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))  # Default to 8:00 AM
        form_layout.addRow("时间:", self.time_edit) # Use form_layout.addRow

        # Days selection
        self.days_group = QGroupBox("提醒日期")
        # Use QHBoxLayout for horizontal arrangement inside the group box
        days_h_layout = QHBoxLayout(self.days_group)
        days_h_layout.setSpacing(10) # Add spacing between checkboxes

        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day in days:
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)  # Default to all days selected
            self.day_checkboxes.append(checkbox)
            days_h_layout.addWidget(checkbox) # Add checkbox to the horizontal layout

        # Add the days group box spanning both columns in the form layout
        form_layout.addRow("", self.days_group) # Add days group with an empty label

        # Create button
        self.create_button = QPushButton("创建提醒")
        self.create_button.setObjectName("add_button")  # Use 'add_button' style
        self.create_button.setIcon(QIcon(":/icons/plus.svg"))
        self.create_button.setIconSize(QSize(16, 16))
        self.create_button.clicked.connect(self.create_reminder)
        # Add the button spanning both columns in the form layout
        form_layout.addRow(self.create_button) # Add button directly to form_layout

    def setup_reminder_list(self):
        """Set up the reminder list."""
        self.reminder_list_group = QGroupBox("当前提醒")
        self.reminder_list_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        list_layout = QVBoxLayout(self.reminder_list_group)
        list_layout.setContentsMargins(10, 25, 10, 10) # Added top margin (25)

        # Reminder table
        self.reminder_table = QTableWidget()
        self.reminder_table.setColumnCount(5)
        self.reminder_table.setHorizontalHeaderLabels(["挑战", "时间", "日期", "状态", "操作"])
        self.reminder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reminder_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.reminder_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.reminder_table.setAlternatingRowColors(True)

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

        # Get user's reminders
        reminders = self.reminder_scheduler.get_user_reminders(self.current_user["id"])

        # Clear table
        self.reminder_table.setRowCount(0)

        # Add reminders to table
        for i, reminder in enumerate(reminders):
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

            # Action button
            delete_button = QPushButton("删除")
            delete_button.setObjectName("delete_button")  # Set object name for styling
            delete_button.setIcon(QIcon(":/icons/trash-2.svg"))
            delete_button.setIconSize(QSize(16, 16))
            delete_button.clicked.connect(
                lambda checked, r=reminder: self.delete_reminder(r["id"])
            )
            self.reminder_table.setCellWidget(i, 4, delete_button)

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
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "创建失败",
                "您还没有订阅任何挑战，请先订阅挑战。"
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
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "创建失败",
                "请至少选择一天进行提醒。"
            )
            return

        # Create reminder
        reminder_id = self.reminder_scheduler.create_reminder(
            self.current_user["id"],
            challenge_id,
            time_str,
            days
        )

        if reminder_id:
            # Show success message non-modally using AnimatedMessageBox
            challenge_title = self.challenge_combo.currentText()
            day_names = self.get_day_names(days)

            create_success_msg = AnimatedMessageBox(self) # Use AnimatedMessageBox
            create_success_msg.setWindowTitle("创建成功")
            create_success_msg.setText(f"已成功创建{challenge_title}的提醒。\n提醒时间: {time_str}\n提醒日期: {', '.join(day_names)}")
            create_success_msg.setIcon(QMessageBox.Information)
            create_success_msg.showNonModal() # Use custom non-modal method

            # Reload reminders
            self.load_reminders()
        else:
            # Failure warning using AnimatedMessageBox
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "创建失败",
                "创建提醒失败，请稍后重试。"
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

        enabled = state == Qt.Checked

        success = self.reminder_scheduler.update_reminder(
            reminder_id,
            enabled=enabled
        )

        if not success:
            AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                self,
                "更新失败",
                "更新提醒状态失败，请稍后重试。"
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
        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
            self,
            "删除提醒",
            "确定要删除这个提醒吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.reminder_scheduler.delete_reminder(reminder_id)

            if success:
                # Reload reminders
                self.load_reminders()
            else:
                AnimatedMessageBox.showWarning( # Use AnimatedMessageBox.showWarning
                    self,
                    "删除失败",
                    "删除提醒失败，请稍后重试。"
                )

    def setup_theme_settings(self):
        """设置主题设置部分"""
        self.theme_settings_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout(self.theme_settings_group)
        theme_layout.setContentsMargins(10, 25, 10, 15)
        theme_layout.setSpacing(15)

        # 主题模式选择（深色/浅色）
        theme_mode_label = QLabel("主题模式:")
        theme_layout.addWidget(theme_mode_label)

        theme_mode_layout = QHBoxLayout()
        theme_mode_layout.setSpacing(20)

        # 创建单选按钮组
        self.theme_mode_group = QButtonGroup(self)

        # 系统默认选项
        self.system_theme_radio = QRadioButton("跟随系统")
        self.light_theme_radio = QRadioButton("浅色模式")
        self.dark_theme_radio = QRadioButton("深色模式")

        # 根据当前主题选中相应的单选按钮
        if self.theme_manager:
            if self.theme_manager.follow_system:
                self.system_theme_radio.setChecked(True)
            elif self.theme_manager.current_theme == "light":
                self.light_theme_radio.setChecked(True)
            else:
                self.dark_theme_radio.setChecked(True)

        # 添加到按钮组
        self.theme_mode_group.addButton(self.system_theme_radio)
        self.theme_mode_group.addButton(self.light_theme_radio)
        self.theme_mode_group.addButton(self.dark_theme_radio)

        # 添加到布局
        theme_mode_layout.addWidget(self.system_theme_radio)
        theme_mode_layout.addWidget(self.light_theme_radio)
        theme_mode_layout.addWidget(self.dark_theme_radio)
        theme_layout.addLayout(theme_mode_layout)

        # 主题样式选择（标准/温馨）
        theme_style_label = QLabel("主题风格:")
        theme_layout.addWidget(theme_style_label)

        theme_style_layout = QHBoxLayout()
        theme_style_layout.setSpacing(20)

        # 创建单选按钮组
        self.theme_style_group = QButtonGroup(self)

        self.standard_style_radio = QRadioButton("标准风格")
        self.warm_style_radio = QRadioButton("温馨风格")

        # 根据当前样式选中相应的单选按钮
        if self.theme_manager:
            if self.theme_manager.theme_style == "warm":
                self.warm_style_radio.setChecked(True)
            else:
                self.standard_style_radio.setChecked(True)

        # 添加到按钮组
        self.theme_style_group.addButton(self.standard_style_radio)
        self.theme_style_group.addButton(self.warm_style_radio)

        # 添加到布局
        theme_style_layout.addWidget(self.standard_style_radio)
        theme_style_layout.addWidget(self.warm_style_radio)
        theme_layout.addLayout(theme_style_layout)

        # 应用按钮
        self.apply_theme_button = QPushButton("应用主题设置")
        self.apply_theme_button.clicked.connect(self.apply_theme_settings)
        theme_layout.addWidget(self.apply_theme_button)

        # 连接信号
        self.theme_mode_group.buttonClicked.connect(self.on_theme_mode_changed)
        self.theme_style_group.buttonClicked.connect(self.on_theme_style_changed)

    def on_theme_mode_changed(self, button):
        """当主题模式改变时调用"""
        # 这里只是记录选择，实际应用在点击应用按钮时进行
        pass

    def on_theme_style_changed(self, button):
        """当主题样式改变时调用"""
        # 这里只是记录选择，实际应用在点击应用按钮时进行
        pass

    def apply_theme_settings(self):
        """应用主题设置"""
        if not self.theme_manager:
            return

        # 获取选中的主题模式
        if self.system_theme_radio.isChecked():
            # 设置为跟随系统
            self.theme_manager.follow_system = True
            # 检测系统主题
            self.theme_manager.detect_system_theme()
        else:
            # 设置为手动选择
            self.theme_manager.follow_system = False
            if self.light_theme_radio.isChecked():
                self.theme_manager.current_theme = "light"
            else:
                self.theme_manager.current_theme = "dark"

        # 获取选中的主题样式
        if self.standard_style_radio.isChecked():
            self.theme_manager.theme_style = "standard"
        else:
            self.theme_manager.theme_style = "warm"

        # 应用主题
        self.theme_manager.apply_theme()

        # 显示成功消息
        AnimatedMessageBox.showInformation(
            self,
            "主题设置",
            "主题设置已应用成功！"
        )

        # 发送主题变更信号
        self.theme_changed.emit(self.theme_manager.current_theme, self.theme_manager.theme_style)

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
