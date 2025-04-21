from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTimeEdit, QComboBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, Slot, QTime
from PySide6.QtGui import QFont

import datetime


class ReminderWidget(QWidget):
    """
    Widget for managing reminders.
    """

    def __init__(self, reminder_scheduler, challenge_manager):
        """
        Initialize the reminder widget.

        Args:
            reminder_scheduler: Reminder scheduler instance
            challenge_manager: Challenge manager instance
        """
        super().__init__()

        self.reminder_scheduler = reminder_scheduler
        self.challenge_manager = challenge_manager
        self.current_user = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        self.title_label = QLabel("提醒设置")
        self.title_label.setFont(QFont("Helvetica Neue", 20, QFont.Bold))  # Adjusted font
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("设置善行挑战的提醒，帮助您坚持完成挑战")
        self.main_layout.addWidget(self.subtitle_label)

        self.main_layout.addSpacing(20)

        # Content layout
        self.content_layout = QHBoxLayout()

        # Create reminder form
        self.setup_reminder_form()
        self.content_layout.addWidget(self.reminder_form_group)

        # Reminder list
        self.setup_reminder_list()
        self.content_layout.addWidget(self.reminder_list_group)

        self.main_layout.addLayout(self.content_layout)

    def setup_reminder_form(self):
        """Set up the reminder creation form."""
        self.reminder_form_group = QGroupBox("创建新提醒")
        self.reminder_form_group.setMinimumWidth(300)
        self.reminder_form_group.setMaximumWidth(400)

        form_layout = QFormLayout(self.reminder_form_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setSpacing(15)

        # Challenge selection
        self.challenge_combo = QComboBox()
        self.challenge_combo.setMinimumWidth(200)
        form_layout.addRow("挑战:", self.challenge_combo)

        # Time selection
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 0))  # Default to 8:00 AM
        form_layout.addRow("时间:", self.time_edit)

        # Days selection
        self.days_group = QGroupBox("提醒日期")
        days_layout = QVBoxLayout(self.days_group)

        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)  # Default to all days selected
            self.day_checkboxes.append(checkbox)
            days_layout.addWidget(checkbox)

        form_layout.addRow("", self.days_group)

        # Create button
        self.create_button = QPushButton("创建提醒")
        self.create_button.clicked.connect(self.create_reminder)
        form_layout.addRow("", self.create_button)

    def setup_reminder_list(self):
        """Set up the reminder list."""
        self.reminder_list_group = QGroupBox("当前提醒")

        list_layout = QVBoxLayout(self.reminder_list_group)

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
            QMessageBox.warning(
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
            QMessageBox.warning(
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
            # Show success message
            challenge_title = self.challenge_combo.currentText()
            day_names = self.get_day_names(days)

            QMessageBox.information(
                self,
                "创建成功",
                f"已成功创建{challenge_title}的提醒。\n"
                f"提醒时间: {time_str}\n"
                f"提醒日期: {', '.join(day_names)}"
            )

            # Reload reminders
            self.load_reminders()
        else:
            QMessageBox.warning(
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
            QMessageBox.warning(
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

        # Ask for confirmation
        reply = QMessageBox.question(
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
                QMessageBox.warning(
                    self,
                    "删除失败",
                    "删除提醒失败，请稍后重试。"
                )

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
