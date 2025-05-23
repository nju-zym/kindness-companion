import logging
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QPushButton,
    QLabel,
    QMessageBox,
    QButtonGroup,
    QSizePolicy,
    QApplication,
    QLineEdit,
    QTextEdit,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QFontMetrics,
    QPainterPath,
    QLinearGradient,
    QFontDatabase,
    QIconEngine,
)
from typing import Optional, Any

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox

from .user_auth import LoginWidget, RegisterWidget
from .challenge_ui import ChallengeListWidget
from .checkin_ui import CheckinWidget
from .progress_ui import ProgressWidget
from .reminder_ui import ReminderWidget
from .profile_ui import ProfileWidget
from .community_ui import CommunityWidget
from .pet_ui import PetWidget  # Import PetWidget

# 定义主题颜色
THEME_COLORS = {
    "light": {
        "background": "#F5F5DC",
        "surface": "#FFFFFF",
        "primary": "#98FF98",
        "primary_hover": "#7FFF7F",
        "text": "#333333",
        "text_secondary": "#666666",
        "border": "#E6E6E6",
        "accent": "#E67E22",
    },
    "dark": {
        "background": "#1A1A1A",
        "surface": "#2D2D2D",
        "primary": "#4CAF50",
        "primary_hover": "#45A049",
        "text": "#FFFFFF",
        "text_secondary": "#B3B3B3",
        "border": "#404040",
        "accent": "#FF9800",
    },
}

class ChevronIcon(QIcon):
    """自定义箭头图标类"""
    def __init__(self, direction="right"):
        super().__init__()
        self.direction = direction
        self.addPixmap(self.create_chevron_pixmap())

    def create_chevron_pixmap(self):
        """创建箭头图标的像素图"""
        size = QSize(24, 24)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor("#666666"))
        painter.setPen(pen)
        
        # 绘制箭头
        path = QPainterPath()
        if self.direction == "right":
            path.moveTo(9, 6)
            path.lineTo(15, 12)
            path.lineTo(9, 18)
        else:  # left
            path.moveTo(15, 6)
            path.lineTo(9, 12)
            path.lineTo(15, 18)
        
        painter.drawPath(path)
        painter.end()
        
        return pixmap

class MainWindow(QMainWindow):
    """
    Main application window with navigation and content areas.
    """

    # Signal to notify when user logs in or out
    user_changed = Signal(dict)

    def __init__(
        self,
        user_manager,
        challenge_manager,
        progress_tracker,
        reminder_scheduler,
        wall_manager,
        theme_manager,
        ai_manager,
    ):
        """
        Initialize the main window.

        Args:
            user_manager: User manager instance
            challenge_manager: Challenge manager instance
            progress_tracker: Progress tracker instance
            reminder_scheduler: Reminder scheduler instance
            wall_manager: Wall manager instance
            theme_manager: Theme manager instance
            ai_manager: AI manager instance
        """
        super().__init__()

        # 设置当前主题
        self.current_theme = "light"  # 默认使用浅色主题

        # 设置日志记录器
        self.logger = logging.getLogger("kindness_challenge.main_window")

        # Store backend managers
        self.user_manager = user_manager
        self.challenge_manager = challenge_manager
        self.progress_tracker = progress_tracker
        self.reminder_scheduler = reminder_scheduler
        self.wall_manager = wall_manager
        self.theme_manager = theme_manager
        self.ai_manager = ai_manager

        # 设置窗口标题和大小
        self.setWindowTitle("Kindness Companion")
        self.resize(1200, 800)

        # 设置窗口大小变化时的响应
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.adjust_layout_for_size)

        # Set up reminder callback
        self.reminder_scheduler.set_callback(self.show_reminder)

        # 获取屏幕尺寸，设置窗口为屏幕的一定比例
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.75)  # 窗口宽度为屏幕宽度的75%
        height = int(screen.height() * 0.75)

        # 设置最小尺寸，确保在小屏幕上也有合理的显示
        self.setMinimumSize(min(800, width), min(600, height))

        # 设置初始大小
        self.resize(width, height)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("main_central_widget")

        # 创建主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # 创建导航栏和宠物区域（初始隐藏）
        self.setup_navigation()  # 导航栏会添加到最左侧
        self.setup_content_area()  # 内容区域会添加到中间
        self.setup_pet_area()  # 宠物区域会添加到最右侧

        # Connect signals
        self.connect_signals()

        # 尝试自动登录
        self.attempt_auto_login()

    def setup_navigation(self):
        """Set up the navigation sidebar."""
        # 创建一个容器来包裹导航栏
        self.nav_container = QWidget()
        self.nav_container.setObjectName("nav_container")
        nav_container_layout = QVBoxLayout(self.nav_container)
        nav_container_layout.setContentsMargins(0, 0, 0, 0)
        nav_container_layout.setSpacing(0)

        # 创建导航栏内容容器
        self.nav_content = QWidget()
        nav_content_layout = QVBoxLayout(self.nav_content)
        nav_content_layout.setContentsMargins(0, 0, 0, 0)
        nav_content_layout.setSpacing(0)

        # 创建导航栏
        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("nav_widget")
        self.nav_widget.setMinimumWidth(220)  # 设置最小宽度
        self.nav_widget.setMaximumWidth(280)  # 设置最大宽度

        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nav_layout.setContentsMargins(15, 30, 15, 30)
        self.nav_layout.setSpacing(20)

        # 创建一个容器控件来包含标题标签
        self.title_container = QWidget()
        self.title_container.setMinimumHeight(80)  # 增加容器高度，使标题更加突出
        self.title_layout = QVBoxLayout(self.title_container)
        self.title_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App title
        self.title_label = QLabel("善行伴侣")
        self.title_label.setObjectName("title_label")  # Set object name
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 设置字体并显式指定大小
        title_font = QFont("Hiragino Sans GB", 24, QFont.Weight.Bold)  # 增加字体大小
        self.title_label.setFont(title_font)
        self.title_label.setMinimumHeight(60)  # 增加高度
        self.title_label.setStyleSheet(
            "padding: 8px; margin: 0px; color: #E67E22;"
        )  # 可选：如需完全交给QSS，也可移除

        # 添加标题到容器并显式设置大小策略
        self.title_layout.addWidget(self.title_label)
        self.title_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # 添加主题切换按钮
        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setMinimumWidth(90)
        self.theme_toggle_btn.setMaximumWidth(140)
        self.theme_toggle_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.update_theme_toggle_btn()
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.title_layout.addWidget(self.theme_toggle_btn)

        # 添加标题容器到导航布局
        self.nav_layout.addWidget(self.title_container)
        self.nav_layout.addSpacing(15)  # 增加标题下方的空间

        # Navigation buttons
        self.nav_buttons = {}
        self.nav_button_group = QButtonGroup(
            self
        )  # Use QButtonGroup for exclusive selection
        self.nav_button_group.setExclusive(True)

        # Define navigation items with icons
        nav_items = [
            ("challenges", "挑战列表", self.show_challenges, ":/icons/list.svg"),
            ("checkin", "每日打卡", self.show_checkin, ":/icons/check-square.svg"),
            ("progress", "我的进度", self.show_progress, ":/icons/calendar-check.svg"),
            ("reminders", "提醒设置", self.show_reminders, ":/icons/bell.svg"),
            ("community", "善意墙", self.show_community, ":/icons/users.svg"),
            ("profile", "个人信息", self.show_profile, ":/icons/user.svg"),
        ]

        icon_size = QSize(24, 24)  # 增加图标尺寸

        for item_id, label, callback, icon_path in nav_items:
            button = QPushButton(label)
            button.setObjectName(f"nav_button_{item_id}")
            button.setMinimumHeight(56)  # 增加按钮高度
            button.setCursor(Qt.CursorShape.PointingHandCursor)  # 添加手型光标

            # 设置按钮样式
            # button.setStyleSheet(...)  # 移除

            if icon_path:
                try:
                    icon = QIcon(icon_path)
                    if icon.isNull():
                        print(f"Warning: Icon not found at {icon_path}")
                    button.setIcon(icon)
                    button.setIconSize(icon_size)
                except Exception as e:
                    print(f"Error loading icon {icon_path}: {e}")

            button.setCheckable(True)
            button.clicked.connect(callback)
            button.clicked.connect(lambda _, b=button: self.update_button_style(b))
            self.nav_buttons[item_id] = button
            self.nav_button_group.addButton(button)

            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.nav_layout.addWidget(button)
            button.setEnabled(False)  # Disabled until login

        # Add stretch to push logout button to bottom
        self.nav_layout.addStretch()

        # 将导航栏添加到容器
        nav_content_layout.addWidget(self.nav_widget)
        nav_container_layout.addWidget(self.nav_content)
        
        # 将导航容器添加到主布局的最左侧
        self.main_layout.insertWidget(0, self.nav_container, 1)  # 使用 insertWidget 确保在最左侧

    def apply_theme(self, theme="light"):
        """移除，全部交由全局QSS管理"""
        pass

    def setup_content_area(self):
        """Set up the content area with stacked widget."""
        self.content_widget = QStackedWidget()
        self.content_widget.setObjectName("content_widget")

        # 应用当前主题
        self.apply_theme(self.current_theme)

        # Create and add widgets to stacked widget
        self.login_widget = LoginWidget(self.user_manager)
        self.register_widget = RegisterWidget(self.user_manager)
        self.challenge_widget = ChallengeListWidget(
            self.challenge_manager, self.progress_tracker
        )
        self.checkin_widget = CheckinWidget(
            self.progress_tracker, self.challenge_manager
        )

        # 创建进度页面并放入滚动区域
        self.progress_widget = ProgressWidget(
            self.progress_tracker, self.challenge_manager
        )
        self.progress_scroll_area = QScrollArea()
        self.progress_scroll_area.setWidgetResizable(True)
        self.progress_scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # 移除边框
        self.progress_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )  # 禁用水平滚动
        self.progress_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )  # 需要时显示垂直滚动条
        self.progress_scroll_area.setWidget(self.progress_widget)

        # 获取主题管理器
        app = QApplication.instance()
        theme_manager = None
        if app:
            theme_manager = app.property("theme_manager")
            if theme_manager:
                self.logger.info("成功获取应用程序实例中的主题管理器")
            else:
                self.logger.warning("无法获取主题管理器属性")
        else:
            self.logger.warning(
                "无法获取应用程序实例中的主题管理器，主题设置功能将不可用"
            )

        self.reminder_widget = ReminderWidget(
            self.reminder_scheduler, self.challenge_manager, theme_manager
        )
        self.community_widget = CommunityWidget(self.wall_manager, self.user_manager)
        self.profile_widget = ProfileWidget(
            self.user_manager, self.progress_tracker, self.challenge_manager
        )

        # Add widgets to stacked widget
        self.content_widget.addWidget(self.login_widget)
        self.content_widget.addWidget(self.register_widget)
        self.content_widget.addWidget(self.challenge_widget)
        self.content_widget.addWidget(self.checkin_widget)
        self.content_widget.addWidget(
            self.progress_scroll_area
        )  # 使用滚动区域替代直接添加progress_widget
        self.content_widget.addWidget(self.reminder_widget)
        self.content_widget.addWidget(self.community_widget)
        self.content_widget.addWidget(self.profile_widget)

        # 将内容区域添加到主布局的中间
        self.main_layout.insertWidget(1, self.content_widget, 3)  # 使用 insertWidget 确保在中间位置

    def setup_pet_area(self):
        """Sets up the area for the PetWidget."""
        # 创建一个容器来包裹宠物区域和折叠按钮
        self.pet_area_container = QWidget()
        self.pet_area_container.setObjectName("pet_area_container")
        pet_area_layout = QHBoxLayout(self.pet_area_container)
        pet_area_layout.setContentsMargins(0, 0, 0, 0)
        pet_area_layout.setSpacing(0)

        # 创建宠物区域容器
        self.pet_container = QWidget()
        self.pet_container.setObjectName("pet_container")
        self.pet_container.setMinimumWidth(260)  # 设置最小宽度
        self.pet_container.setMaximumWidth(320)  # 设置最大宽度

        # 为容器创建布局
        self.pet_container_layout = QVBoxLayout(self.pet_container)
        self.pet_container_layout.setContentsMargins(20, 30, 20, 30)
        self.pet_container_layout.setSpacing(20)
        self.pet_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 实例化宠物部件
        self.pet_widget = PetWidget(self.user_manager)  # Instantiate PetWidget
        self.pet_widget.setObjectName("pet_widget_area")  # For potential styling

        # 将宠物部件添加到容器布局中
        self.pet_container_layout.addWidget(self.pet_widget)

        # 将宠物区域容器添加到主布局的最右侧
        self.main_layout.insertWidget(2, self.pet_area_container, 1)  # 使用 insertWidget 确保在最右侧
        pet_area_layout.addWidget(self.pet_container)

    def connect_signals(self):
        """Connect signals between widgets."""
        # Connect login signals
        self.login_widget.login_successful.connect(self.on_login_successful)
        self.login_widget.register_requested.connect(self.show_register)

        # Connect register signals
        self.register_widget.register_successful.connect(self.on_register_successful)
        self.register_widget.login_requested.connect(self.show_login)

        # Connect user_changed signal to widgets
        self.user_changed.connect(self.challenge_widget.set_user)
        self.user_changed.connect(self.checkin_widget.set_user)
        self.user_changed.connect(self.progress_widget.set_user)
        self.user_changed.connect(self.reminder_widget.set_user)
        self.user_changed.connect(self.community_widget.set_user)
        self.user_changed.connect(self.profile_widget.set_user)
        self.user_changed.connect(self.pet_widget.set_user)

        # Connect profile widget signals
        self.profile_widget.user_updated.connect(self.update_user_info)
        self.profile_widget.user_logged_out.connect(self.handle_logout)

        # 连接主题变更信号
        if hasattr(self.reminder_widget, "theme_changed"):
            self.reminder_widget.theme_changed.connect(self.handle_theme_changed)

        # Connect challenge subscription changed to checkin refresh
        self.challenge_widget.challenge_subscription_changed.connect(
            self.checkin_widget.load_checkable_challenges
        )
        # 新增：打卡成功后自动刷新进度并跳转到进度页
        self.checkin_widget.check_in_successful.connect(self.on_checkin_successful)

    @Slot(dict)
    def on_login_successful(self, user):
        """
        Handle successful login.

        Args:
            user (dict): User information
        """
        logging.info("Login successful, preparing UI updates...")
        
        # 显示导航栏和宠物区域（包括它们的容器）
        self.nav_container.show()
        self.pet_area_container.show()
        
        # Enable navigation buttons
        for button in self.nav_buttons.values():
            button.setEnabled(True)
            button.style().unpolish(button)
            button.style().polish(button)

        # Emit user_changed signal
        self.user_changed.emit(user)

        # Show challenges page and set its button as checked
        logging.info("Calling show_challenges...")
        self.show_challenges()
        logging.info("Returned from show_challenges.")

        if "challenges" in self.nav_buttons:
            self.nav_buttons["challenges"].setChecked(True)
            self.update_button_style(self.nav_buttons["challenges"])

        # Show a non-modal animated welcome message
        welcome_msg = AnimatedMessageBox(self)
        welcome_msg.setWindowTitle("登录成功")
        welcome_msg.setText(f"欢迎回来，{user['username']}！\n准备好今天的善行挑战了吗？")
        welcome_msg.setIcon(QMessageBox.Icon.Information)
        welcome_msg.showNonModal()
        logging.info("Non-modal animated welcome message shown.")

    @Slot(dict)
    def on_register_successful(self, user):
        """
        Handle successful registration.

        Args:
            user (dict): User information
        """
        self.show_login()

        # Show success message non-modally using AnimatedMessageBox
        reg_success_msg = AnimatedMessageBox(self)  # Use AnimatedMessageBox
        reg_success_msg.setWindowTitle("注册成功")
        reg_success_msg.setText(
            f"欢迎加入善行伴侣，{user['username']}！\n请使用您的新账号登录。"
        )
        reg_success_msg.setIcon(QMessageBox.Icon.Information)
        reg_success_msg.showNonModal()  # Use custom non-modal method

    def logout(self):
        """Log out the current user."""
        self.user_manager.logout()

        # 隐藏导航栏和宠物区域（包括它们的容器）
        self.nav_container.hide()
        self.pet_area_container.hide()

        # Disable navigation buttons
        for button in self.nav_buttons.values():
            button.setEnabled(False)
            button.style().unpolish(button)
            button.style().polish(button)

        # Uncheck all nav buttons
        checked_button = self.nav_button_group.checkedButton()
        if checked_button:
            self.nav_button_group.setExclusive(False)
            checked_button.setChecked(False)
            self.nav_button_group.setExclusive(True)
            self.update_button_style(checked_button)

        # Emit user_changed signal with None
        self.user_changed.emit(None)

        # Show login page
        self.show_login()

    def show_login(self):
        """Show the login page."""
        self.content_widget.setCurrentWidget(self.login_widget)

    def show_register(self):
        """Show the registration page."""
        self.content_widget.setCurrentWidget(self.register_widget)

    def show_challenges(self):
        """Show the challenges page."""
        logging.info(
            f"Attempting to switch to challenge_widget. Current widget: {self.content_widget.currentWidget()}"
        )
        self.content_widget.setCurrentWidget(self.challenge_widget)
        logging.info(
            f"Switched content widget. Current widget is now: {self.content_widget.currentWidget()}"
        )

    def show_checkin(self):
        """Show the check-in page."""
        self.content_widget.setCurrentWidget(self.checkin_widget)

    def show_progress(self):
        """Show the progress page."""
        self.progress_widget.load_progress()  # 每次切换都刷新
        self.content_widget.setCurrentWidget(self.progress_scroll_area)

    def show_reminders(self):
        """Show the reminders page."""
        self.content_widget.setCurrentWidget(self.reminder_widget)

    def show_community(self):
        """Show the community page."""
        self.content_widget.setCurrentWidget(self.community_widget)

    def show_profile(self):
        """Show the profile page."""
        self.content_widget.setCurrentWidget(self.profile_widget)

    def show_reminder(self, reminder):
        """
        Show a reminder notification with options to dismiss or disable.

        Args:
            reminder (dict): Reminder information
        """
        reminder_msg = AnimatedMessageBox(self)
        reminder_msg.setWindowTitle("善行提醒")
        reminder_msg.setText(f"别忘了今天的善行伴侣：\n{reminder['challenge_title']}")
        reminder_msg.setIcon(QMessageBox.Icon.Information)

        # Add custom buttons
        dismiss_button = reminder_msg.addButton(
            "知道了", QMessageBox.ButtonRole.AcceptRole
        )
        dont_show_button = reminder_msg.addButton(
            "不再提醒", QMessageBox.ButtonRole.ActionRole
        )

        # Show non-modally but don't auto-close
        reminder_msg.setModal(False)
        reminder_msg.show()

        # Connect to clicked button signal to handle user choice
        reminder_msg.buttonClicked.connect(
            lambda button: self._handle_reminder_response(
                button, reminder_msg, reminder, dont_show_button
            )
        )

    def update_button_style(self, clicked_button=None):
        """Updates the style of navigation buttons based on the checked state."""
        for item_id, button in self.nav_buttons.items():
            is_checked = (
                button == clicked_button and button.isCheckable() and button.isChecked()
            )
            button.setProperty("selected", is_checked)
            button.style().unpolish(button)
            button.style().polish(button)

    def update_user_info(self, user_info):
        """
        Update user information in the application.

        Args:
            user_info (dict): Updated user information
        """
        self.user_changed.emit(user_info)

    def handle_logout(self):
        """Handle logout triggered from the profile widget."""
        self.logout()

    @Slot(str, str)
    def handle_theme_changed(self, theme_type, theme_style):
        """
        处理主题变更事件

        Args:
            theme_type (str): 主题类型（light/dark）
            theme_style (str): 主题样式（standard/warm）
        """
        # 应用新主题
        self.apply_theme(theme_type)

        # 显示主题变更成功消息
        theme_msg = AnimatedMessageBox(self)
        theme_msg.setWindowTitle("主题已更新")

        theme_type_text = "浅色" if theme_type == "light" else "深色"
        theme_style_text = "温馨" if theme_style == "warm" else "标准"

        theme_msg.setText(f"已切换到{theme_style_text}{theme_type_text}主题")
        theme_msg.setIcon(QMessageBox.Icon.Information)
        theme_msg.showNonModal()

    def _handle_reminder_response(
        self, clicked_button, message_box, reminder, dont_show_button
    ):
        """
        Handle user response to a reminder notification.

        Args:
            clicked_button: The button that was clicked
            message_box: The message box instance
            reminder (dict): The reminder information
            dont_show_button: The "Don't show again" button reference
        """
        # If user clicked "Don't show again"
        if clicked_button == dont_show_button:
            # Disable the reminder in the database
            success = self.reminder_scheduler.update_reminder(
                reminder["id"], enabled=False
            )

            if success:
                # Show confirmation message
                confirm_msg = AnimatedMessageBox(self)
                confirm_msg.setWindowTitle("提醒已禁用")
                confirm_msg.setText(
                    f"已禁用\"{reminder['challenge_title']}\"的提醒。\n您可以在提醒设置中重新启用。"
                )
                confirm_msg.setIcon(QMessageBox.Icon.Information)
                confirm_msg.showNonModal()
            else:
                # Show error message
                error_msg = AnimatedMessageBox(self)
                error_msg.setWindowTitle("操作失败")
                error_msg.setText("禁用提醒失败，请稍后重试。")
                error_msg.setIcon(QMessageBox.Icon.Warning)
                error_msg.showNonModal()

    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        # 使用计时器延迟执行布局调整，避免频繁调整
        self.timer.start(200)  # 200毫秒后执行布局调整

    def adjust_layout_for_size(self):
        """根据窗口大小调整布局，实现响应式设计"""
        width = self.width()
        height = self.height()

        # 计算基础缩放因子 - 基于窗口尺寸与参考尺寸的比例
        # 参考尺寸为 1200x800
        width_scale = width / 1200.0
        height_scale = height / 800.0

        # 使用较小的缩放因子，确保UI元素不会过大
        scale_factor = min(width_scale, height_scale)

        # 限制缩放范围，避免过小或过大
        scale_factor = max(0.7, min(scale_factor, 1.3))

        # 根据窗口宽度调整布局比例
        if width < 1000:  # 窄窗口
            # 调整主布局的比例，确保导航栏在最左侧
            self.main_layout.setStretch(0, 1)  # 导航区域（最左侧）
            self.main_layout.setStretch(1, 3)  # 内容区域（中间）
            self.main_layout.setStretch(2, 1)  # 宠物区域（最右侧）

            # 调整内容区域的内边距，使其在小窗口中更紧凑
            self.content_widget.setContentsMargins(
                int(20 * scale_factor),
                int(20 * scale_factor),
                int(20 * scale_factor),
                int(20 * scale_factor),
            )

            # 调整导航区域的内边距
            self.nav_layout.setContentsMargins(
                int(10 * scale_factor),
                int(20 * scale_factor),
                int(10 * scale_factor),
                int(20 * scale_factor),
            )

            # 调整宠物区域的内边距
            self.pet_container_layout.setContentsMargins(
                int(10 * scale_factor),
                int(20 * scale_factor),
                int(10 * scale_factor),
                int(20 * scale_factor),
            )

        elif width < 1400:  # 中等窗口
            # 调整主布局的比例，确保导航栏在最左侧
            self.main_layout.setStretch(0, 1)  # 导航区域（最左侧）
            self.main_layout.setStretch(1, 3)  # 内容区域（中间）
            self.main_layout.setStretch(2, 1)  # 宠物区域（最右侧）

            # 调整内容区域的内边距
            self.content_widget.setContentsMargins(
                int(20 * scale_factor),
                int(20 * scale_factor),
                int(20 * scale_factor),
                int(20 * scale_factor),
            )

            # 调整导航区域的内边距
            self.nav_layout.setContentsMargins(
                int(10 * scale_factor),
                int(20 * scale_factor),
                int(10 * scale_factor),
                int(20 * scale_factor),
            )

            # 调整宠物区域的内边距
            self.pet_container_layout.setContentsMargins(
                int(15 * scale_factor),
                int(20 * scale_factor),
                int(15 * scale_factor),
                int(20 * scale_factor),
            )

        else:  # 宽窗口
            # 调整主布局的比例，确保导航栏在最左侧
            self.main_layout.setStretch(0, 1)  # 导航区域（最左侧）
            self.main_layout.setStretch(1, 4)  # 内容区域（中间）
            self.main_layout.setStretch(2, 1)  # 宠物区域（最右侧）

            # 调整内容区域的内边距
            self.content_widget.setContentsMargins(
                int(30 * scale_factor),
                int(30 * scale_factor),
                int(30 * scale_factor),
                int(30 * scale_factor),
            )

            # 调整导航区域的内边距
            self.nav_layout.setContentsMargins(
                int(15 * scale_factor),
                int(30 * scale_factor),
                int(15 * scale_factor),
                int(30 * scale_factor),
            )

            # 调整宠物区域的内边距
            self.pet_container_layout.setContentsMargins(
                int(20 * scale_factor),
                int(30 * scale_factor),
                int(20 * scale_factor),
                int(30 * scale_factor),
            )

        # 调整字体大小 - 基于缩放因子
        base_font_size = 10  # 基础字体大小
        font = self.font()

        if width < 1000:  # 窄窗口
            adjusted_size = int(base_font_size * scale_factor * 1.2)  # 窄窗口字体稍大
        elif width < 1400:  # 中等窗口
            adjusted_size = int(base_font_size * scale_factor * 1.4)  # 中等窗口字体更大
        else:  # 宽窗口
            adjusted_size = int(base_font_size * scale_factor * 1.6)  # 宽窗口字体最大

        # 确保字体大小在合理范围内
        adjusted_size = max(9, min(adjusted_size, 18))
        font.setPointSize(adjusted_size)
        self.setFont(font)

        # 调整主布局的间距
        self.main_layout.setSpacing(int(8 * scale_factor))
        self.main_layout.setContentsMargins(
            int(10 * scale_factor),
            int(10 * scale_factor),
            int(10 * scale_factor),
            int(10 * scale_factor),
        )

        # 更新挑战列表布局
        if hasattr(self, "challenge_widget") and self.challenge_widget:
            # 根据窗口宽度调整挑战卡片的列数
            if (
                hasattr(self.challenge_widget, "challenges_layout")
                and self.challenge_widget.challenges_layout
            ):
                if width < 1200:
                    max_cols = 1  # 窄窗口只显示一列
                else:
                    max_cols = 2  # 宽窗口显示两列

                # 重新布局挑战卡片
                if (
                    hasattr(self.challenge_widget, "challenge_cards")
                    and self.challenge_widget.challenge_cards
                ):
                    row, col = 0, 0
                    for card_id, card in self.challenge_widget.challenge_cards.items():
                        if card.isVisible():
                            self.challenge_widget.challenges_layout.addWidget(
                                card, row, col
                            )
                            col += 1
                            if col >= max_cols:
                                col = 0
                                row += 1

    def update_theme_toggle_btn(self):
        """根据当前主题更新主题切换按钮的图标、文本和提示"""
        app = QApplication.instance()
        theme_manager = None
        if app:
            theme_manager = app.property("theme_manager")
        theme = theme_manager.current_theme if theme_manager else self.current_theme
        if theme == "light":
            self.theme_toggle_btn.setIcon(QIcon(":/icons/sun.svg"))
            self.theme_toggle_btn.setText("浅色")
            self.theme_toggle_btn.setToolTip("点击切换到深色模式")
        else:
            self.theme_toggle_btn.setIcon(QIcon(":/icons/moon.svg"))
            self.theme_toggle_btn.setText("深色")
            self.theme_toggle_btn.setToolTip("点击切换到浅色模式")
        self.theme_toggle_btn.setIconSize(QSize(24, 24))

    def toggle_theme(self):
        """切换浅色/深色主题"""
        app = QApplication.instance()
        theme_manager = None
        if app:
            theme_manager = app.property("theme_manager")
        if theme_manager:
            new_theme = "dark" if theme_manager.current_theme == "light" else "light"
            theme_manager.current_theme = new_theme
            theme_manager.apply_theme()
            self.update_theme_toggle_btn()
            self.update()  # 强制刷新界面

    @Slot(int)
    def on_checkin_successful(self, challenge_id):
        self.progress_widget.load_progress()
        self.show_progress()

    def attempt_auto_login(self):
        """尝试自动登录"""
        try:
            # 尝试使用保存的登录状态自动登录
            user = self.user_manager.auto_login()
            if user:
                self.logger.info(f"自动登录成功: {user['username']}")
                # 更新界面状态
                self.on_login_successful(user)
            else:
                self.logger.info("没有保存的登录状态或自动登录失败")
                # 显示登录界面
                self.content_widget.setCurrentWidget(self.login_widget)
        except Exception as e:
            self.logger.error(f"自动登录时发生错误: {e}")
            # 显示登录界面
            self.content_widget.setCurrentWidget(self.login_widget)
