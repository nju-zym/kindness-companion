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
        self.main_layout.setContentsMargins(25, 25, 25, 25)  # Increased margins for better spacing

        # Header
        self.title_label = QLabel("设置")
        self.title_label.setObjectName("title_label")  # Set object name for styling
        self.title_label.setProperty("class", "page_title")  # Add class for styling
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("管理应用设置和提醒")
        self.subtitle_label.setObjectName("subtitle_label")  # Set object name for styling
        self.main_layout.addWidget(self.subtitle_label)

        self.main_layout.addSpacing(20)  # Increased spacing for better separation

        # Content layout with scroll area for better handling of content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame border

        # Container widget for scroll area
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setSpacing(25)  # Increased spacing between sections
        self.content_layout.setContentsMargins(5, 5, 5, 5)  # Small content margins

        # 添加主题设置部分
        if self.theme_manager:
            self.setup_theme_settings()
            self.content_layout.addWidget(self.theme_settings_group)

        # Create reminder form (Challenge, Time, Create Button)
        self.setup_reminder_form()
        self.content_layout.addWidget(self.reminder_form_group)

        # Add Days Group Box directly to the content layout AFTER the form group
        # self.days_group is created in setup_reminder_form
        self.content_layout.addWidget(self.days_group)

        # Reminder list
        self.setup_reminder_list()
        self.content_layout.addWidget(self.reminder_list_group)

        # Set the scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)

        # Add stretch at the end to push content upwards if space allows
        self.content_layout.addStretch()

    def setup_reminder_form(self):
        """Set up the reminder creation form using QFormLayout."""
        self.reminder_form_group = QGroupBox("创建新提醒")
        self.reminder_form_group.setObjectName("reminder_form_group")

        # 使用网格布局以获得更好的对齐效果
        form_layout = QGridLayout(self.reminder_form_group)
        form_layout.setContentsMargins(15, 25, 15, 20)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)

        # 挑战选择标签
        challenge_label = QLabel("挑战:")
        challenge_label.setObjectName("settings_label")
        challenge_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(challenge_label, 0, 0)

        # 挑战选择下拉框
        self.challenge_combo = QComboBox()
        self.challenge_combo.setObjectName("challenge_combo")
        self.challenge_combo.setMinimumWidth(250)
        self.challenge_combo.setMinimumHeight(32)
        form_layout.addWidget(self.challenge_combo, 0, 1)

        # 时间选择标签
        time_label = QLabel("时间:")
        time_label.setObjectName("settings_label")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(time_label, 1, 0)

        # 时间选择编辑框
        self.time_edit = QTimeEdit()
        self.time_edit.setObjectName("time_edit")
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))  # 默认为上午8:00
        self.time_edit.setMinimumHeight(32)
        form_layout.addWidget(self.time_edit, 1, 1)

        # 提醒日期组
        self.days_group = QGroupBox("提醒日期")
        self.days_group.setObjectName("days_group")

        # 使用网格布局来排列复选框，使其更加紧凑
        days_grid_layout = QGridLayout(self.days_group)
        days_grid_layout.setContentsMargins(15, 20, 15, 15)
        days_grid_layout.setHorizontalSpacing(15)
        days_grid_layout.setVerticalSpacing(10)

        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        # 在一行中放置所有复选框
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setObjectName(f"day_checkbox_{i}")
            checkbox.setChecked(True)  # 默认选中所有日期
            self.day_checkboxes.append(checkbox)
            days_grid_layout.addWidget(checkbox, 0, i)

        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 创建按钮
        self.create_button = QPushButton("创建提醒")
        self.create_button.setObjectName("add_button")  # 使用'add_button'样式
        self.create_button.setIcon(QIcon(":/icons/plus.svg"))
        self.create_button.setIconSize(QSize(16, 16))
        self.create_button.setMinimumHeight(32)  # 增加按钮高度
        self.create_button.setMaximumWidth(150)  # 限制按钮宽度
        self.create_button.clicked.connect(self.create_reminder)

        button_layout.addStretch(1)  # 添加弹性空间将按钮推到右侧
        button_layout.addWidget(self.create_button)

        # 将按钮容器添加到表单布局
        form_layout.addWidget(button_container, 2, 0, 1, 2)

    def setup_reminder_list(self):
        """Set up the reminder list."""
        self.reminder_list_group = QGroupBox("当前提醒")
        self.reminder_list_group.setObjectName("reminder_list_group")
        self.reminder_list_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        list_layout = QVBoxLayout(self.reminder_list_group)
        list_layout.setContentsMargins(15, 25, 15, 15)  # 增加边距
        list_layout.setSpacing(15)  # 增加间距

        # 提醒表格
        self.reminder_table = QTableWidget()
        self.reminder_table.setObjectName("reminder_table")
        self.reminder_table.setColumnCount(5)
        self.reminder_table.setHorizontalHeaderLabels(["挑战", "时间", "日期", "状态", "操作"])

        # 设置表头样式
        header = self.reminder_table.horizontalHeader()
        header.setObjectName("reminder_table_header")
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 设置列宽比例
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 挑战列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)    # 时间列固定宽度
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 日期列自适应宽度
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # 状态列固定宽度
        header.setSectionResizeMode(4, QHeaderView.Fixed)    # 操作列固定宽度

        # 设置固定列的宽度
        self.reminder_table.setColumnWidth(1, 80)   # 时间列宽度
        self.reminder_table.setColumnWidth(3, 80)   # 状态列宽度
        self.reminder_table.setColumnWidth(4, 100)  # 操作列宽度

        # 其他表格设置
        self.reminder_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 不可编辑
        self.reminder_table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        self.reminder_table.setAlternatingRowColors(True)  # 交替行颜色
        self.reminder_table.setShowGrid(True)  # 显示网格线
        self.reminder_table.setGridStyle(Qt.SolidLine)  # 实线网格

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
            delete_button.clicked.connect(lambda _, rid=reminder_id: self.delete_reminder(rid))

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
            print(f"User confirmed deletion of reminder ID: {reminder_id}")

            # Get reminder info before deletion for debugging
            reminder_info = self.reminder_scheduler.get_user_reminders(self.current_user["id"])
            reminder_to_delete = None
            for reminder in reminder_info:
                if reminder["id"] == reminder_id:
                    reminder_to_delete = reminder
                    break

            if reminder_to_delete:
                print(f"Found reminder to delete: {reminder_to_delete}")
            else:
                print(f"Warning: Reminder ID {reminder_id} not found in user's reminders")

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
                    self,
                    "删除成功",
                    f"已成功删除提醒。"
                )
            else:
                # Show detailed error message with debugging info
                error_message = "删除提醒失败，请稍后重试。"
                if reminder_to_delete:
                    error_message += f"\n\n调试信息：\n提醒ID: {reminder_id}\n挑战: {reminder_to_delete['challenge_title']}"

                AnimatedMessageBox.showWarning(
                    self,
                    "删除失败",
                    error_message
                )

    def setup_theme_settings(self):
        """设置主题设置部分"""
        self.theme_settings_group = QGroupBox("主题设置")
        self.theme_settings_group.setObjectName("theme_settings_group")

        # 使用网格布局以获得更好的对齐效果
        theme_layout = QGridLayout(self.theme_settings_group)
        theme_layout.setContentsMargins(15, 25, 15, 20)
        theme_layout.setSpacing(15)
        theme_layout.setVerticalSpacing(20)  # 增加垂直间距

        # 主题模式选择（深色/浅色）
        theme_mode_label = QLabel("主题模式:")
        theme_mode_label.setObjectName("settings_label")
        theme_layout.addWidget(theme_mode_label, 0, 0)

        # 创建单选按钮组
        self.theme_mode_group = QButtonGroup(self)

        # 创建一个水平布局来容纳单选按钮
        mode_container = QWidget()
        theme_mode_layout = QHBoxLayout(mode_container)
        theme_mode_layout.setContentsMargins(0, 0, 0, 0)
        theme_mode_layout.setSpacing(25)  # 增加按钮间距

        # 系统默认选项
        self.system_theme_radio = QRadioButton("跟随系统")
        self.light_theme_radio = QRadioButton("浅色模式")
        self.dark_theme_radio = QRadioButton("深色模式")

        # 设置单选按钮的对象名称以便样式化
        self.system_theme_radio.setObjectName("system_theme_radio")
        self.light_theme_radio.setObjectName("light_theme_radio")
        self.dark_theme_radio.setObjectName("dark_theme_radio")

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
        theme_mode_layout.addStretch(1)  # 添加弹性空间

        # 将单选按钮容器添加到网格布局
        theme_layout.addWidget(mode_container, 0, 1)

        # 主题样式选择（标准/温馨/Sourcio）
        theme_style_label = QLabel("主题风格:")
        theme_style_label.setObjectName("settings_label")
        theme_layout.addWidget(theme_style_label, 1, 0)

        # 创建单选按钮组
        self.theme_style_group = QButtonGroup(self)

        # 创建一个水平布局来容纳单选按钮
        style_container = QWidget()
        theme_style_layout = QHBoxLayout(style_container)
        theme_style_layout.setContentsMargins(0, 0, 0, 0)
        theme_style_layout.setSpacing(25)  # 增加按钮间距

        self.standard_style_radio = QRadioButton("标准风格")
        self.warm_style_radio = QRadioButton("温馨风格")
        self.sourcio_style_radio = QRadioButton("Sourcio风格")

        # 设置单选按钮的对象名称以便样式化
        self.standard_style_radio.setObjectName("standard_style_radio")
        self.warm_style_radio.setObjectName("warm_style_radio")
        self.sourcio_style_radio.setObjectName("sourcio_style_radio")

        # 根据当前样式选中相应的单选按钮
        if self.theme_manager:
            if self.theme_manager.theme_style == "warm":
                self.warm_style_radio.setChecked(True)
            elif self.theme_manager.theme_style == "sourcio":
                self.sourcio_style_radio.setChecked(True)
            else:
                self.standard_style_radio.setChecked(True)

        # 添加到按钮组
        self.theme_style_group.addButton(self.standard_style_radio)
        self.theme_style_group.addButton(self.warm_style_radio)
        self.theme_style_group.addButton(self.sourcio_style_radio)

        # 添加到布局
        theme_style_layout.addWidget(self.standard_style_radio)
        theme_style_layout.addWidget(self.warm_style_radio)
        theme_style_layout.addWidget(self.sourcio_style_radio)
        theme_style_layout.addStretch(1)  # 添加弹性空间

        # 将单选按钮容器添加到网格布局
        theme_layout.addWidget(style_container, 1, 1)

        # 应用按钮 - 放在右侧
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.apply_theme_button = QPushButton("应用主题设置")
        self.apply_theme_button.setObjectName("apply_theme_button")
        self.apply_theme_button.setMinimumHeight(32)  # 增加按钮高度
        self.apply_theme_button.setMaximumWidth(150)  # 限制按钮宽度
        self.apply_theme_button.clicked.connect(self.apply_theme_settings)

        button_layout.addStretch(1)  # 添加弹性空间将按钮推到右侧
        button_layout.addWidget(self.apply_theme_button)

        # 将按钮容器添加到网格布局的第三行，跨越两列
        theme_layout.addWidget(button_container, 2, 0, 1, 2)

        # 连接信号
        self.theme_mode_group.buttonClicked.connect(self.on_theme_mode_changed)
        self.theme_style_group.buttonClicked.connect(self.on_theme_style_changed)

    def on_theme_mode_changed(self, _):
        """当主题模式改变时调用"""
        # 这里只是记录选择，实际应用在点击应用按钮时进行
        pass

    def on_theme_style_changed(self, _):
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
            # 检测系统主题并应用
            current_system_theme = self.theme_manager.detect_system_theme()
            self.theme_manager.current_theme = current_system_theme
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
        elif self.warm_style_radio.isChecked():
            self.theme_manager.theme_style = "warm"
        elif self.sourcio_style_radio.isChecked():
            self.theme_manager.theme_style = "sourcio"
        else:
            # 默认使用 standard 样式
            self.theme_manager.theme_style = "standard"
            self.standard_style_radio.setChecked(True) # 确保UI同步

        # 应用主题
        self.theme_manager.apply_theme()

        # 显示成功消息
        theme_type_text = "跟随系统" if self.theme_manager.follow_system else ("浅色" if self.theme_manager.current_theme == "light" else "深色")
        theme_style_text = "温馨" if self.theme_manager.theme_style == "warm" else ("Sourcio" if self.theme_manager.theme_style == "sourcio" else "标准")

        AnimatedMessageBox.showInformation(
            self,
            "主题设置",
            f"已应用{theme_style_text}{theme_type_text}主题！"
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
