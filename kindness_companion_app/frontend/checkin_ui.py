from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton, QFormLayout, QMessageBox,
    QListWidget, QListWidgetItem # Import QListWidget and QListWidgetItem
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QIcon
import datetime

# Import AnimatedMessageBox
from .widgets.animated_message_box import AnimatedMessageBox


class CheckinWidget(QWidget):
    """
    Widget for daily check-in and reflection.
    """
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

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(18)

        self.title_label = QLabel("📅 每日打卡与反思")
        self.title_label.setObjectName("title_label")
        layout.addWidget(self.title_label)

        # --- Check-in Form (Modified) ---
        # Use QVBoxLayout instead of QFormLayout for more flexibility
        form_area_layout = QVBoxLayout()
        form_area_layout.setSpacing(12)

        # Challenge Selection Label
        self.challenge_label = QLabel("选择要打卡的挑战:")
        form_area_layout.addWidget(self.challenge_label)

        # Challenge List (Replaces QComboBox)
        self.challenge_list = QListWidget()
        self.challenge_list.setMinimumHeight(100) # Adjust height as needed
        self.challenge_list.setObjectName("challenge_list") # For styling
        form_area_layout.addWidget(self.challenge_list)

        # Reflection Notes Label
        self.notes_label = QLabel("今日感想:")
        form_area_layout.addWidget(self.notes_label)

        # Reflection Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("记录一下今天的感想吧...(可选)")
        self.notes_edit.setMinimumHeight(80)
        form_area_layout.addWidget(self.notes_edit)

        layout.addLayout(form_area_layout)

        # Check-in Button
        self.checkin_button = QPushButton(" 确认打卡")
        self.checkin_button.setObjectName("checkin_button")
        self.checkin_button.setMinimumHeight(45) # Slightly taller button
        # --- Add Icon ---
        checkin_icon = QIcon(":/icons/check-circle.svg") # Use resource path
        if not checkin_icon.isNull():
             self.checkin_button.setIcon(checkin_icon)
             self.checkin_button.setIconSize(QSize(20, 20)) # Adjust icon size as needed
        else:
             print("Warning: Could not load check-in button icon.") # Or use logging
        # --- End Add Icon ---
        self.checkin_button.clicked.connect(self.submit_checkin)
        layout.addWidget(self.checkin_button, alignment=Qt.AlignRight)

        layout.addStretch() # Push elements to the top

        # Initially disable form until user is set and challenges loaded
        self.challenge_list.setEnabled(False)
        self.notes_edit.setEnabled(False)
        self.checkin_button.setEnabled(False)

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
            self.notes_edit.setEnabled(True) # Enable notes field
        else:
            # Clear UI elements and disable
            self.challenge_list.clear()
            # Add a placeholder item when logged out
            placeholder_item = QListWidgetItem("请先登录")
            placeholder_item.setFlags(Qt.NoItemFlags) # Make it non-selectable
            self.challenge_list.addItem(placeholder_item)
            self.challenge_list.setEnabled(False)

            self.notes_edit.clear()
            self.notes_edit.setEnabled(False)
            self.checkin_button.setEnabled(False)

    def load_checkable_challenges(self):
        """Load challenges that the user is subscribed to and can check in for today into the QListWidget."""
        if not self.current_user:
            self.challenge_list.setEnabled(False)
            self.checkin_button.setEnabled(False)
            return

        self.challenge_list.clear()
        self.challenge_list.setEnabled(False) # Disable while loading
        self.checkin_button.setEnabled(False)

        # Add a temporary loading item
        loading_item = QListWidgetItem("加载挑战中...")
        loading_item.setFlags(Qt.NoItemFlags) # Make it non-selectable
        self.challenge_list.addItem(loading_item)

        subscribed_challenges = self.challenge_manager.get_user_challenges(self.current_user["id"])
        today = datetime.date.today().isoformat()
        checkable_challenges = []

        for challenge in subscribed_challenges:
            check_ins_today = self.progress_tracker.get_check_ins(
                self.current_user["id"], challenge["id"], today, today
            )
            if not check_ins_today:
                checkable_challenges.append(challenge)

        self.challenge_list.clear() # Clear loading item

        if checkable_challenges:
            self.challenge_list.setEnabled(True)
            self.checkin_button.setEnabled(True)
            for challenge in checkable_challenges:
                item = QListWidgetItem(challenge["title"])
                item.setData(Qt.UserRole, challenge["id"]) # Store ID as data
                self.challenge_list.addItem(item)
            # Select the first item by default if list is not empty
            if self.challenge_list.count() > 0:
                self.challenge_list.setCurrentRow(0)
        else:
            placeholder_item = QListWidgetItem("今日已全部打卡或未订阅挑战")
            placeholder_item.setFlags(Qt.NoItemFlags) # Make it non-selectable
            self.challenge_list.addItem(placeholder_item)
            self.challenge_list.setEnabled(False)
            self.checkin_button.setEnabled(False)

    @Slot()
    def submit_checkin(self):
        """Handle the check-in submission."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "用户未登录")
            return

        # Get selected item from QListWidget
        selected_item = self.challenge_list.currentItem()
        notes = self.notes_edit.toPlainText().strip()

        if selected_item is None or selected_item.flags() == Qt.NoItemFlags:
            AnimatedMessageBox.showWarning(self, "打卡失败", "请选择一个要打卡的挑战")
            return

        challenge_id = selected_item.data(Qt.UserRole)
        challenge_title = selected_item.text()

        if challenge_id is None: # Should not happen if item is selectable, but check anyway
             AnimatedMessageBox.showWarning(self, "打卡失败", "无法获取所选挑战的信息")
             return

        # Perform check-in using progress_tracker
        success = self.progress_tracker.check_in(
            self.current_user["id"],
            challenge_id,
            notes=notes if notes else None
        )

        if success:
            # --- Get current streak ---
            try:
                current_streak = self.progress_tracker.get_streak(self.current_user["id"], challenge_id)
                streak_message = f"\n\n🔥 当前连续打卡: {current_streak} 天！"
            except Exception as e:
                print(f"Error getting streak: {e}")
                streak_message = "" # Don't show streak if there's an error
            # --- End Get current streak ---

            # --- Update success message ---
            AnimatedMessageBox.showInformation(
                self,
                "打卡成功!",
                f"已成功为 '{challenge_title}' 打卡！{streak_message}"
            )
            # --- End Update success message ---

            # Clear notes and reload challenges
            self.notes_edit.clear()
            self.load_checkable_challenges()
            # TODO: Consider emitting a signal here if other UIs need to update immediately
            # self.checkin_successful.emit(challenge_id)
        else:
            # This might happen if there's a race condition or DB error
            AnimatedMessageBox.showWarning(self, "打卡失败", "无法完成打卡，请稍后重试或检查是否已打卡。")
            # Reload to ensure consistency
            self.load_checkable_challenges()
