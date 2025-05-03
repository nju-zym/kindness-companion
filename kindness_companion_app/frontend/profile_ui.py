# TODO: 实现用户设置界面 (未来可扩展)
import os
import logging # Add this import at the top
from pathlib import Path
from datetime import datetime # Import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QGroupBox, QFrame,
    QGridLayout, QProgressBar, QSizePolicy, QTextEdit,
    QFileDialog, QScrollArea, QSpacerItem, QInputDialog, QCheckBox # Added QCheckBox
)
# Import QByteArray and potentially QBuffer, QIODevice for resizing
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QBitmap, QPainterPath
# shutil might not be needed anymore if we don't copy files
# import shutil

# Import the custom message box
from .widgets.animated_message_box import AnimatedMessageBox
from .password_dialog import PasswordDialog


class ProfileWidget(QWidget):
    """
    Widget for displaying and editing user profile.
    """
    # Define signals
    user_updated = Signal(dict)
    user_logged_out = Signal()

    def __init__(self, user_manager, progress_tracker, challenge_manager):
        """
        Initialize the profile widget.

        Args:
            user_manager: User manager instance
            progress_tracker: Progress tracker instance
            challenge_manager: Challenge manager instance
        """
        # ... (初始化保持不变)
        super().__init__()

        self.user_manager = user_manager
        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user = None

        # 初始化新 UI 元素
        self.avatar_label = None
        self.username_label = None
        self.reg_date_label = None
        self.bio_display_label = None
        self.bio_edit = None
        self.edit_bio_button = None
        self.save_bio_button = None
        self.cancel_bio_button = None
        # Add elements for dynamic achievements
        self.achievements_group = None
        self.achievements_scroll_area = None
        self.achievements_container = None
        self.achievements_layout = None
        self.achievements_placeholder = None
        self.achievements_spacer = None

        self._is_toggling_consent = False # Add processing flag

        self.setup_ui()

    # ... (setup_ui, setup_profile_info remain largely the same) ...
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)  # Increased margins for better spacing
        self.main_layout.setSpacing(25)  # Increased spacing between elements

        # 重新设计的标题区域
        title_frame = QFrame()
        title_frame.setObjectName("title_frame")
        title_frame.setStyleSheet("""
            QFrame#title_frame {
                background-color: rgba(40, 40, 40, 0.95);  /* 更深的背景色 */
                border-radius: 18px;  /* 增加圆角 */
                padding: 15px;  /* 增加内边距 */
                margin-bottom: 25px;  /* 增加底部边距 */
                border: 1px solid rgba(80, 80, 80, 0.8);  /* 添加边框 */
            }
        """)

        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 12, 15, 12)

        # Add an icon to the title
        icon_label = QLabel()
        icon = QIcon(":/icons/user.svg")
        if not icon.isNull():
            pixmap = icon.pixmap(QSize(32, 32))  # 更大的图标
            icon_label.setPixmap(pixmap)
        title_layout.addWidget(icon_label)

        # 标题文本 - 更加突出
        self.title_label = QLabel("个人信息")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel#title_label {
                font-size: 28px;  /* 更大的字体 */
                font-weight: bold;
                color: #FF9800;  /* 明亮的橙色 */
                padding: 10px;  /* 增加内边距 */
                letter-spacing: 1.5px;  /* 增加字间距 */
            }
        """)
        title_layout.addWidget(self.title_label)

        self.main_layout.addWidget(title_frame)

        # 创建一个滚动区域来包含所有内容，确保在任何缩放比例下都能正常显示
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内容区域调整大小
        scroll_area.setFrameShape(QFrame.NoFrame)  # 移除边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示垂直滚动条
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(30, 30, 30, 0.5);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(80, 80, 80, 0.7);
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar:horizontal {
                background: rgba(30, 30, 30, 0.5);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(80, 80, 80, 0.7);
                min-width: 20px;
                border-radius: 6px;
            }
        """)

        # 创建内容容器
        content_container = QWidget()
        content_container.setObjectName("content_container")
        content_container.setStyleSheet("""
            QWidget#content_container {
                background-color: rgba(30, 30, 30, 0.7);
                border-radius: 18px;
                border: 1px solid rgba(70, 70, 70, 0.8);
            }
        """)

        # 为容器创建布局
        container_layout = QVBoxLayout(content_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)  # 确保元素之间有足够的间距

        # 使用水平布局代替网格布局，更好地控制元素大小
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(20)  # 增加元素间距
        self.content_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距，由容器提供

        # 设置最小宽度以确保内容不会被压缩得太小
        content_container.setMinimumWidth(800)

        # 先创建两个部分
        self.setup_profile_info()
        self.setup_stats()

        # 添加到水平布局中
        self.content_layout.addWidget(self.profile_group, 40)  # 40% 的宽度
        self.content_layout.addWidget(self.stats_group, 60)    # 60% 的宽度

        # 将内容布局添加到容器布局
        container_layout.addLayout(self.content_layout)

        # 设置滚动区域的内容
        scroll_area.setWidget(content_container)

        # 将滚动区域添加到主布局
        self.main_layout.addWidget(scroll_area)

        # Add action buttons
        self.setup_action_buttons()

    def setup_profile_info(self):
        """Set up the profile information section."""
        self.profile_group = QGroupBox("基本信息")
        self.profile_group.setObjectName("profile_group")
        self.profile_group.setStyleSheet("""
            QGroupBox#profile_group {
                font-weight: bold;
                font-size: 22px;  /* 更大的字体 */
                border-radius: 18px;  /* 增加圆角 */
                background-color: rgba(35, 35, 35, 0.9);  /* 更深的背景色 */
                border: 1px solid rgba(80, 80, 80, 0.7);  /* 更明显的边框 */
                padding-top: 35px;  /* 为标题留出更多空间 */
                color: #FF9800;  /* 标题使用橙色 */
            }
        """)
        # 设置尺寸策略，使其能够在水平和垂直方向上都能灵活调整大小
        self.profile_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小宽度，确保内容不会被压缩得太小
        self.profile_group.setMinimumWidth(300)

        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setContentsMargins(25, 30, 25, 25)  # Increased margins
        profile_layout.setSpacing(25)  # Increased spacing between elements

        # --- 重新设计的头像区域 ---
        # 创建一个更加突出的头像容器
        avatar_frame = QFrame()
        avatar_frame.setObjectName("avatar_frame")
        avatar_frame.setStyleSheet("""
            QFrame#avatar_frame {
                background-color: rgba(45, 45, 45, 0.8);  /* 稍微深一点的背景 */
                border-radius: 24px;  /* 更大的圆角 */
                padding: 25px;  /* 增加内边距 */
                border: 1px solid rgba(90, 90, 90, 0.7);  /* 更明显的边框 */
                margin: 8px;  /* 添加外边距 */
            }
        """)

        # 使用网格布局，更好地控制头像和用户信息的位置
        avatar_layout = QGridLayout(avatar_frame)
        avatar_layout.setContentsMargins(15, 15, 15, 15)
        avatar_layout.setSpacing(15)  # 适当的间距
        avatar_layout.setColumnStretch(0, 1)  # 头像列
        avatar_layout.setColumnStretch(1, 2)  # 用户信息列

        # 头像容器 - 使用框架包装以便更好地控制布局
        avatar_container_frame = QFrame()
        avatar_container_frame.setObjectName("avatar_container")
        avatar_container_frame.setStyleSheet("""
            QFrame#avatar_container {
                background-color: transparent;
                border: none;
            }
        """)

        # 头像容器布局
        avatar_container = QVBoxLayout(avatar_container_frame)
        avatar_container.setAlignment(Qt.AlignCenter)
        avatar_container.setContentsMargins(5, 5, 5, 5)  # 减小内边距
        avatar_container.setSpacing(10)  # 减小间距

        # 自适应大小的头像
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatar_label")
        self.avatar_label.setMinimumSize(140, 140)  # 更大的最小尺寸
        self.avatar_label.setMaximumSize(180, 180)  # 更大的最大尺寸
        self.avatar_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许扩展
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel#avatar_label {
                border: 3px solid #FF9800;  /* 橙色边框 */
                border-radius: 90px;  /* 圆形头像 */
                background-color: #333333;  /* 深灰色背景 */
                padding: 3px;  /* 内边距 */
            }
        """)
        # Default avatar set in set_user or reset_stats

        # 更新头像按钮样式
        self.change_avatar_button = QPushButton("更换头像")
        self.change_avatar_button.setIcon(QIcon(":/icons/image.svg"))
        self.change_avatar_button.setIconSize(QSize(18, 18))  # 稍大的图标
        self.change_avatar_button.clicked.connect(self.change_avatar)
        self.change_avatar_button.setMinimumHeight(36)  # 更高的按钮
        self.change_avatar_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.change_avatar_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: #222;
                border-radius: 18px;  /* 圆角按钮 */
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FFA726;
            }
            QPushButton:pressed {
                background-color: #FB8C00;
            }
        """)

        # 添加头像到容器
        avatar_container.addWidget(self.avatar_label, 0, Qt.AlignCenter)

        # 更新头像按钮 - 更小更紧凑
        self.change_avatar_button = QPushButton("更换头像")
        self.change_avatar_button.setIcon(QIcon(":/icons/image.svg"))
        self.change_avatar_button.setIconSize(QSize(16, 16))
        self.change_avatar_button.clicked.connect(self.change_avatar)
        self.change_avatar_button.setFixedHeight(32)  # 固定高度
        self.change_avatar_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.change_avatar_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: #222;
                border-radius: 16px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFA726;
            }
            QPushButton:pressed {
                background-color: #FB8C00;
            }
        """)

        # 添加按钮到容器
        avatar_container.addWidget(self.change_avatar_button, 0, Qt.AlignCenter)

        # 添加头像容器到网格布局的第一列
        avatar_layout.addWidget(avatar_container_frame, 0, 0, Qt.AlignCenter)

        # 右侧用户信息区域 - 使用框架包装
        user_info_frame = QFrame()
        user_info_frame.setObjectName("user_info_frame")
        user_info_frame.setStyleSheet("""
            QFrame#user_info_frame {
                background-color: rgba(35, 35, 35, 0.5);
                border-radius: 10px;
                border: 1px solid rgba(60, 60, 60, 0.5);
                padding: 5px;
            }
        """)

        # 用户信息布局
        user_info_container = QVBoxLayout(user_info_frame)
        user_info_container.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        user_info_container.setContentsMargins(10, 10, 10, 10)
        user_info_container.setSpacing(8)

        # 用户名标签 - 大号字体
        username_title = QLabel("用户名")
        username_title.setStyleSheet("color: #bbb; font-size: 16px; font-weight: bold;")
        user_info_container.addWidget(username_title)

        # 用户名值 - 突出显示
        self.username_label = QLabel("N/A")
        self.username_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 24px;")
        self.username_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.username_label.setWordWrap(True)  # 允许文本换行
        user_info_container.addWidget(self.username_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555; margin: 8px 0;")
        separator.setMaximumHeight(2)
        user_info_container.addWidget(separator)

        # 注册日期标签
        reg_date_title = QLabel("注册日期")
        reg_date_title.setStyleSheet("color: #bbb; font-size: 16px; font-weight: bold;")
        user_info_container.addWidget(reg_date_title)

        # 注册日期值
        self.reg_date_label = QLabel("N/A")
        self.reg_date_label.setStyleSheet("font-weight: bold; color: #4FC3F7; font-size: 20px;")
        user_info_container.addWidget(self.reg_date_label)

        # 添加用户信息框架到网格布局的第二列
        avatar_layout.addWidget(user_info_frame, 0, 1)

        # 添加头像框架到个人资料布局
        profile_layout.addWidget(avatar_frame)

        # 我们已经将用户信息整合到头像区域，不再需要单独的用户信息区域

        # --- 重新设计的个人简介区域 ---
        bio_frame = QFrame()
        bio_frame.setObjectName("bio_frame")
        bio_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 允许水平扩展
        bio_frame.setStyleSheet("""
            QFrame#bio_frame {
                background-color: rgba(40, 40, 40, 0.7);  /* 稍微深一点的背景 */
                border-radius: 15px;  /* 圆角 */
                padding: 15px;  /* 内边距 */
                border: 1px solid rgba(80, 80, 80, 0.6);  /* 更明显的边框 */
                margin: 5px;  /* 添加外边距 */
            }
        """)

        bio_layout = QVBoxLayout(bio_frame)
        bio_layout.setContentsMargins(15, 15, 15, 15)  # 适当的内边距
        bio_layout.setSpacing(10)  # 减小间距

        # 带图标的标题区域 - 更紧凑
        bio_header = QHBoxLayout()
        bio_header.setSpacing(8)
        bio_header.setContentsMargins(0, 0, 0, 5)  # 只在底部添加一点边距

        # 添加图标
        bio_icon = QLabel()
        icon = QIcon(":/icons/edit-3.svg")
        if not icon.isNull():
            pixmap = icon.pixmap(QSize(18, 18))
            bio_icon.setPixmap(pixmap)
        bio_header.addWidget(bio_icon)

        # 简介标题
        bio_title = QLabel("个人简介")
        bio_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #FF9800;")
        bio_header.addWidget(bio_title)
        bio_header.addStretch()  # 添加弹性空间，使标题居左

        # 添加编辑按钮到标题行
        self.edit_bio_button = QPushButton("编辑")
        self.edit_bio_button.setIcon(QIcon(":/icons/edit-2.svg"))
        self.edit_bio_button.setIconSize(QSize(16, 16))
        self.edit_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        self.edit_bio_button.setFixedSize(80, 32)  # 更大的按钮
        self.edit_bio_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 16px;
                padding: 5px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFA726;
            }
            QPushButton:pressed {
                background-color: #FB8C00;
            }
        """)
        bio_header.addWidget(self.edit_bio_button)

        bio_layout.addLayout(bio_header)

        # 简介显示区域 - 自适应大小
        self.bio_display_label = QLabel("这个人很神秘，什么也没留下...")
        self.bio_display_label.setObjectName("bio_display")
        self.bio_display_label.setWordWrap(True)
        self.bio_display_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.bio_display_label.setMinimumHeight(100)  # 更大的最小高度
        self.bio_display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许扩展
        self.bio_display_label.setStyleSheet("""
            QLabel#bio_display {
                background-color: rgba(35, 35, 35, 0.9);
                border-radius: 12px;
                padding: 15px;
                color: #f5f5f5;
                font-size: 16px;
                border: 1px solid rgba(80, 80, 80, 0.7);
                line-height: 150%;
            }
        """)

        # 简介编辑区域 - 更紧凑的样式
        self.bio_edit = QTextEdit()
        self.bio_edit.setObjectName("bio_edit")
        self.bio_edit.setPlaceholderText("在这里编辑您的个人简介...")
        self.bio_edit.setVisible(False)  # 初始隐藏
        self.bio_edit.setMinimumHeight(100)  # 更大的最小高度
        self.bio_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许扩展
        self.bio_edit.setStyleSheet("""
            QTextEdit#bio_edit {
                background-color: rgba(35, 35, 35, 0.9);
                border-radius: 12px;
                padding: 15px;
                color: #f5f5f5;
                font-size: 16px;
                border: 2px solid #FF9800;
                line-height: 150%;
            }
        """)

        # 编辑模式按钮布局 - 更紧凑
        bio_button_layout = QHBoxLayout()
        bio_button_layout.setSpacing(8)  # 减小按钮间距
        bio_button_layout.setContentsMargins(0, 5, 0, 0)  # 只在顶部添加一点边距
        bio_button_layout.addStretch(1)  # 右对齐按钮

        # 保存按钮 - 绿色
        self.save_bio_button = QPushButton("保存")
        self.save_bio_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_bio_button.setIconSize(QSize(14, 14))
        self.save_bio_button.setVisible(False)  # 初始隐藏
        self.save_bio_button.clicked.connect(self.save_bio)
        self.save_bio_button.setFixedSize(70, 28)  # 更小的按钮
        self.save_bio_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 14px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
            QPushButton:pressed {
                background-color: #43A047;
            }
        """)

        # 取消按钮 - 红色
        self.cancel_bio_button = QPushButton("取消")
        self.cancel_bio_button.setIcon(QIcon(":/icons/x.svg"))
        self.cancel_bio_button.setIconSize(QSize(14, 14))
        self.cancel_bio_button.setVisible(False)  # 初始隐藏
        self.cancel_bio_button.clicked.connect(lambda: self.toggle_bio_edit())
        self.cancel_bio_button.setFixedSize(70, 28)  # 更小的按钮
        self.cancel_bio_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 14px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
        """)

        # 添加按钮到布局
        bio_button_layout.addWidget(self.cancel_bio_button)
        bio_button_layout.addWidget(self.save_bio_button)

        # Add widgets to bio layout
        bio_layout.addWidget(self.bio_display_label)
        bio_layout.addWidget(self.bio_edit)
        bio_layout.addLayout(bio_button_layout)

        # Add bio frame to profile layout
        profile_layout.addWidget(bio_frame)


        # --- AI Settings Section with improved styling ---
        ai_frame = QFrame()
        ai_frame.setObjectName("ai_frame")
        ai_frame.setStyleSheet("""
            QFrame#ai_frame {
                background-color: rgba(40, 40, 40, 0.5);
                border-radius: 8px;
                padding: 10px;
            }
        """)

        ai_settings_layout = QVBoxLayout(ai_frame)
        ai_settings_layout.setContentsMargins(15, 15, 15, 15)
        ai_settings_layout.setSpacing(12)

        # AI settings title
        ai_title = QLabel("AI 功能设置")
        ai_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #4FC3F7;")
        ai_title.setAlignment(Qt.AlignCenter)
        ai_settings_layout.addWidget(ai_title)

        # AI consent checkbox with improved styling
        self.ai_consent_checkbox = QCheckBox("启用 AI 功能")
        self.ai_consent_checkbox.setObjectName("ai_checkbox")
        self.ai_consent_checkbox.setToolTip("启用或禁用 AI 电子宠物和智能报告功能")
        self.ai_consent_checkbox.stateChanged.connect(self.toggle_ai_consent)
        self.ai_consent_checkbox.setStyleSheet("""
            QCheckBox#ai_checkbox {
                font-weight: bold;
                color: #4FC3F7;
                font-size: 16px;
            }
            QCheckBox#ai_checkbox::indicator {
                width: 22px;
                height: 22px;
            }
        """)

        # AI features explanation with improved styling
        ai_info_frame = QFrame()
        ai_info_frame.setObjectName("ai_info_frame")
        ai_info_frame.setStyleSheet("""
            QFrame#ai_info_frame {
                background-color: rgba(30, 30, 30, 0.7);
                border-radius: 5px;
                padding: 5px;
            }
        """)

        ai_info_layout = QVBoxLayout(ai_info_frame)
        ai_info_layout.setContentsMargins(10, 10, 10, 10)

        ai_info_label = QLabel(
            "启用后，应用将使用 AI 功能增强您的体验：\n"
            "• AI 电子宠物互动\n"
            "• 个性化善举报告\n\n"
            "这需要将部分数据发送至第三方 AI 服务。"
        )
        ai_info_label.setWordWrap(True)
        ai_info_label.setStyleSheet("color: #ddd; font-size: 14px; line-height: 150%;")
        ai_info_layout.addWidget(ai_info_label)

        # Add widgets to layout
        ai_settings_layout.addWidget(self.ai_consent_checkbox)
        ai_settings_layout.addWidget(ai_info_frame)

        # Add AI frame to profile layout
        profile_layout.addWidget(ai_frame)

        # Action buttons will be set up in a separate method
        self.action_button_layout = QVBoxLayout()
        profile_layout.addLayout(self.action_button_layout)

    def setup_action_buttons(self):
        """Set up the action buttons in a separate section."""
        # Clear any existing widgets
        while self.action_button_layout.count():
            item = self.action_button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.action_button_layout.setSpacing(15)  # Ensure equal spacing between all buttons

        # Create a horizontal layout for buttons to be side by side
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Create a frame for the action buttons
        action_frame = QFrame()
        action_frame.setObjectName("action_frame")
        action_frame.setStyleSheet("""
            QFrame#action_frame {
                background-color: rgba(40, 40, 40, 0.5);
                border-radius: 8px;
                padding: 10px;
            }
        """)

        # Layout for the frame
        frame_layout = QVBoxLayout(action_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(15)

        # Add a title to the frame
        title_label = QLabel("账户操作")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)

        # Create a horizontal layout for the main buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Common button style
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
            }
        """

        # Change Password Button
        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setIcon(QIcon(":/icons/lock.svg"))
        self.change_password_button.setIconSize(QSize(22, 22))
        self.change_password_button.setMinimumHeight(48)
        self.change_password_button.clicked.connect(self.show_password_dialog)
        self.change_password_button.setStyleSheet(button_style)
        button_layout.addWidget(self.change_password_button)

        # Logout Button
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("logout_button")
        self.logout_button.setIcon(QIcon(":/icons/log-out.svg"))
        self.logout_button.setIconSize(QSize(22, 22))
        self.logout_button.setMinimumHeight(48)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setStyleSheet(button_style.replace("#2196F3", "#607D8B").replace("#42A5F5", "#78909C").replace("#1E88E5", "#546E7A"))
        button_layout.addWidget(self.logout_button)

        # Add the button layout to the frame
        frame_layout.addLayout(button_layout)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555;")
        separator.setMaximumHeight(1)
        frame_layout.addWidget(separator)

        # Delete Account Button (in its own row)
        self.delete_account_button = QPushButton("注销账号")
        self.delete_account_button.setObjectName("delete_account_button")
        self.delete_account_button.setIcon(QIcon(":/icons/trash-2.svg"))
        self.delete_account_button.setIconSize(QSize(22, 22))
        self.delete_account_button.setMinimumHeight(48)
        self.delete_account_button.clicked.connect(self.request_delete_account)
        self.delete_account_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
        """)
        frame_layout.addWidget(self.delete_account_button)

        # Add the frame to the main action button layout
        self.action_button_layout.addWidget(action_frame)


    def setup_stats(self):
        """设置统计和成就部分。"""
        self.stats_group = QGroupBox("统计与成就")
        self.stats_group.setObjectName("stats_group")
        # 允许统计组垂直和水平扩展
        self.stats_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小宽度，确保内容不会被压缩得太小
        self.stats_group.setMinimumWidth(400)
        self.stats_group.setStyleSheet("""
            QGroupBox#stats_group {
                font-weight: bold;
                font-size: 22px;  /* 更大的字体 */
                border-radius: 18px;  /* 增加圆角 */
                background-color: rgba(35, 35, 35, 0.9);  /* 更深的背景色 */
                border: 1px solid rgba(80, 80, 80, 0.7);  /* 更明显的边框 */
                padding-top: 35px;  /* 为标题留出更多空间 */
                color: #FF9800;  /* 标题使用橙色 */
            }
        """)

        stats_layout = QVBoxLayout(self.stats_group)
        stats_layout.setContentsMargins(25, 30, 25, 25)  # Increased margins
        stats_layout.setSpacing(25)  # Increased spacing

        # --- 重新设计的概览布局 ---
        summary_group = QGroupBox("概览")
        summary_group.setObjectName("summary_group")
        summary_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 允许水平扩展
        summary_group.setStyleSheet("""
            QGroupBox#summary_group {
                font-weight: bold;
                font-size: 16px;  /* 更大的字体 */
                border-radius: 15px;  /* 增加圆角 */
                background-color: rgba(35, 35, 35, 0.7);  /* 稍微亮一点的背景 */
                border: 1px solid rgba(80, 80, 80, 0.6);  /* 更明显的边框 */
                padding-top: 25px;  /* 为标题留出空间 */
                color: #FF9800;  /* 橙色标题 */
                margin: 5px;  /* 添加外边距 */
            }
        """)
        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(20)  # Increase spacing between stats
        summary_layout.setContentsMargins(15, 20, 15, 20)  # Add more padding

        # Create styled stat displays
        def create_stat_display(value, title, icon_path):
            # 创建一个自适应大小的容器框架
            frame = QFrame()
            frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 允许水平扩展
            frame.setObjectName("stat_frame")
            frame.setStyleSheet("""
                QFrame#stat_frame {
                    background-color: rgba(40, 40, 40, 0.7);  /* 稍微深一点的背景 */
                    border-radius: 15px;  /* 增加圆角 */
                    padding: 15px;  /* 增加内边距 */
                    border: 1px solid rgba(80, 80, 80, 0.6);  /* 更明显的边框 */
                    margin: 5px;  /* 添加外边距 */
                }
            """)

            # Vertical layout for the stat
            stat_layout = QVBoxLayout(frame)
            stat_layout.setAlignment(Qt.AlignCenter)
            stat_layout.setContentsMargins(10, 10, 10, 10)  # Added margins
            stat_layout.setSpacing(12)  # Increased spacing

            # Icon at the top
            if icon_path:
                icon_label = QLabel()
                icon = QIcon(icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(QSize(24, 24))
                    icon_label.setPixmap(pixmap)
                    icon_label.setAlignment(Qt.AlignCenter)
                    stat_layout.addWidget(icon_label)

            # 使用更大的字体显示数值
            value_label = QLabel(value)
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 38px; font-weight: bold; color: #FF9800; margin-top: 8px;")  # 更大的字体和更亮的颜色
            stat_layout.addWidget(value_label)

            # 标题标签 - 更清晰的样式
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("color: #f0f0f0; font-size: 18px; margin-top: 10px; font-weight: bold;")  # 更亮的颜色和更大的字体
            stat_layout.addWidget(title_label)

            return frame, value_label

        # Total check-ins
        total_frame, self.total_label = create_stat_display("0", "总打卡次数", ":/icons/check-circle.svg")
        summary_layout.addWidget(total_frame, 0, 0)

        # Longest streak
        streak_frame, self.streak_label = create_stat_display("0", "最长连续打卡", ":/icons/zap.svg")
        summary_layout.addWidget(streak_frame, 0, 1)

        # Challenges
        challenges_frame, self.challenges_label = create_stat_display("0", "已订阅挑战", ":/icons/book-open.svg")
        summary_layout.addWidget(challenges_frame, 0, 2)

        # Set column stretch factors for equal width
        summary_layout.setColumnStretch(0, 1)
        summary_layout.setColumnStretch(1, 1)
        summary_layout.setColumnStretch(2, 1)

        stats_layout.addWidget(summary_group)  # Add the summary group

        # --- 重新设计的成就区域 ---
        self.achievements_group = QGroupBox("我的成就")
        self.achievements_group.setObjectName("achievements_group")
        self.achievements_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许水平和垂直扩展
        self.achievements_group.setStyleSheet("""
            QGroupBox#achievements_group {
                font-weight: bold;
                font-size: 20px;  /* 更大的字体 */
                border-radius: 18px;  /* 增加圆角 */
                background-color: rgba(40, 40, 40, 0.8);  /* 稍微亮一点的背景 */
                border: 1px solid rgba(90, 90, 90, 0.7);  /* 更明显的边框 */
                padding-top: 30px;  /* 为标题留出空间 */
                color: #FF9800;  /* 橙色标题 */
                margin: 8px;  /* 添加外边距 */
            }
        """)
        # 已经设置了 SizePolicy，不需要重复设置
        achievements_group_layout = QVBoxLayout(self.achievements_group)
        achievements_group_layout.setContentsMargins(20, 25, 20, 20)  # Increased padding

        # Scroll Area for Achievements
        self.achievements_scroll_area = QScrollArea()
        self.achievements_scroll_area.setWidgetResizable(True)
        self.achievements_scroll_area.setObjectName("achievements_scroll_area") # For potential styling
        self.achievements_scroll_area.setFrameShape(QFrame.NoFrame) # Remove border

        # Container Widget inside Scroll Area
        self.achievements_container = QWidget()
        self.achievements_scroll_area.setWidget(self.achievements_container)

        # Layout for the Container Widget (where achievements will be added)
        self.achievements_layout = QVBoxLayout(self.achievements_container)
        self.achievements_layout.setAlignment(Qt.AlignTop) # Align items to the top
        self.achievements_layout.setSpacing(8) # Spacing between achievements
        self.achievements_layout.setContentsMargins(5, 5, 5, 5) # Add some padding

        # Placeholder Label
        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setAlignment(Qt.AlignCenter)
        self.achievements_placeholder.setStyleSheet("font-size: 16px; color: #f0f0f0; padding: 20px;")
        self.achievements_layout.addWidget(self.achievements_placeholder)

        # Spacer Item
        self.achievements_spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.achievements_layout.addSpacerItem(self.achievements_spacer)

        achievements_group_layout.addWidget(self.achievements_scroll_area) # Add scroll area to group
        stats_layout.addWidget(self.achievements_group) # Add achievements group to main stats layout


    # ... (_set_circular_avatar, set_user remain the same) ...
    def _set_circular_avatar(self, avatar_data): # Parameter changed to avatar_data (bytes or None)
        """Loads an image from bytes, makes it circular, and sets it on the avatar_label."""
        pixmap = QPixmap()
        loaded = False
        if avatar_data:
            # Load pixmap from byte data
            loaded = pixmap.loadFromData(avatar_data)

        if not loaded:
            # print(f"Warning: Could not load avatar from data. Using default resource.")
            logging.warning(f"Could not load avatar from data. Using default resource.") # Use logging
            # Fallback to default resource if data is None or loading fails
            pixmap = QPixmap(":/images/profilePicture.png")
            if pixmap.isNull():
                 # print("ERROR: Default avatar resource ':/images/profilePicture.png' is also missing!")
                 logging.error("Default avatar resource ':/images/profilePicture.png' is also missing!") # Use logging
                 # Optionally create a plain colored circle as ultimate fallback
                 pixmap = QPixmap(140, 140)  # Updated to match the new avatar size
                 pixmap.fill(Qt.gray)


        # Scale the pixmap first - use larger size to match the new avatar label
        size = 140  # Updated to match the new avatar size
        # Use KeepAspectRatioByExpanding to fill the circle, then clip
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # --- Alternative: Draw clipped pixmap onto a new transparent pixmap ---
        final_pixmap = QPixmap(size, size)
        final_pixmap.fill(Qt.transparent) # Start with a transparent pixmap

        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a circular clipping path
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        # Calculate offsets to draw the scaled pixmap centered
        x_offset = (scaled_pixmap.width() - size) // 2
        y_offset = (scaled_pixmap.height() - size) // 2

        # Draw the (potentially larger) scaled pixmap onto the target pixmap, clipped
        painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
        painter.end()

        # Set the final circular pixmap
        self.avatar_label.setPixmap(final_pixmap)


    @Slot(int)
    def toggle_ai_consent(self, state):
        """
        Toggle AI consent status when the checkbox is clicked.

        Args:
            state (int): Qt.Checked (2) if checked, Qt.Unchecked (0) if unchecked
        """
        # --- Prevent re-entry ---
        if self._is_toggling_consent:
            return
        self._is_toggling_consent = True
        # --- End Prevent re-entry ---

        try: # Use try/finally to ensure flag is reset
            logger = logging.getLogger(__name__)

            if not self.current_user:
                logger.warning("Cannot toggle AI consent: No user logged in")
                return # Exit early

            user_id = self.current_user.get('id')
            if not user_id:
                logger.error("Cannot toggle AI consent: User ID not found")
                return # Exit early

            # Convert checkbox state to boolean
            consent_status = state == Qt.Checked
            logger.info(f"Setting AI consent for user {user_id} to: {consent_status}")

            # Update the database
            success = self.user_manager.set_ai_consent(user_id, consent_status)

            if success:
                # Update the current user object
                self.current_user["ai_consent_given"] = consent_status

                # Show a confirmation message
                if consent_status:
                    AnimatedMessageBox.showInformation(
                        self,
                        "AI 功能已启用",
                        "AI 功能已启用。您现在可以使用 AI 电子宠物和智能报告功能。"
                    )
                else:
                    AnimatedMessageBox.showInformation(
                        self,
                        "AI 功能已禁用",
                        "AI 功能已禁用。应用将不再发送数据至 AI 服务。"
                    )

                # Emit signal to notify other parts of the app
                self.user_updated.emit(self.current_user)
            else:
                # Revert checkbox state if update failed
                self.ai_consent_checkbox.blockSignals(True)
                self.ai_consent_checkbox.setChecked(not consent_status)
                self.ai_consent_checkbox.blockSignals(False)
                AnimatedMessageBox.showWarning(
                    self,
                    "设置失败",
                    "无法更新 AI 功能设置，请稍后重试。"
                )
        finally:
            # --- Reset flag ---
            self._is_toggling_consent = False
            # --- End Reset flag ---

    @Slot(dict)
    def set_user(self, user):
        """Set the current user and update UI elements using avatar data."""
        logger = logging.getLogger(__name__)
        logger.info(f"ProfileWidget.set_user called. User is None: {user is None}")
        self.current_user = user

        if user:
            logger.debug(f"User data: {user}") # Log user data for debugging
            self.username_label.setText(user.get("username", "N/A"))

            # --- Load and Format Registration Date ---
            reg_date_str_raw = user.get("registration_date")
            logger.info(f"Raw registration_date from user dict: '{reg_date_str_raw}' (Type: {type(reg_date_str_raw)})" ) # Log raw value

            final_display_text = "未知" # Default to '未知' if date is missing or invalid within a valid user session

            if reg_date_str_raw:
                try:
                    # Attempt parsing (handle potential extra parts like microseconds or timezone)
                    timestamp_part = str(reg_date_str_raw).split('.')[0].split('+')[0] # More robust splitting
                    dt_object = datetime.strptime(timestamp_part, '%Y-%m-%d %H:%M:%S')
                    final_display_text = dt_object.strftime('%Y-%m-%d')
                    logger.info(f"Successfully parsed and formatted date: {final_display_text}")
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Could not parse registration date '{reg_date_str_raw}': {e}. Falling back to '未知'.")
                    # Keep final_display_text as "未知"
            else:
                # If reg_date_str_raw is None or empty string
                logger.warning("registration_date key missing or value is None/empty in user dict. Setting text to '未知'.")
                # Keep final_display_text as "未知"

            logger.info(f"Final text to set on reg_date_label: '{final_display_text}'")
            self.reg_date_label.setText(final_display_text)
            # --- End Registration Date ---

            # --- Load Bio ---
            bio = user.get("bio", "")
            if bio:
                self.bio_display_label.setText(bio)
                self.bio_edit.setText(bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")
                self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

            # --- Load Avatar from BLOB data ---
            avatar_data = user.get("avatar") # Get bytes or None
            self._set_circular_avatar(avatar_data) # Use the helper method

            # --- Set AI Consent Checkbox ---
            ai_consent = user.get("ai_consent_given")
            logger.info(f"Setting AI consent checkbox based on user data: {ai_consent}")
            # Disconnect signal temporarily to avoid triggering toggle_ai_consent
            self.ai_consent_checkbox.blockSignals(True)
            if ai_consent is True:
                self.ai_consent_checkbox.setChecked(True)
            else:
                self.ai_consent_checkbox.setChecked(False)
            self.ai_consent_checkbox.blockSignals(False)

            # Load stats (which now includes loading achievements)
            self.load_stats()
        else: # User is None (logout or initial state)
            logger.info("User is None. Resetting profile fields to N/A.")
            # Clear profile info
            self.username_label.setText("N/A")
            # Reset reg date to N/A explicitly for logged-out state
            self.reg_date_label.setText("N/A")
            # Reset bio
            self.bio_display_label.setText("请先登录")
            self.bio_edit.setText("")
            self.toggle_bio_edit(edit_mode=False) # Ensure display mode

            # Reset AI consent checkbox
            self.ai_consent_checkbox.blockSignals(True)
            self.ai_consent_checkbox.setChecked(False)
            self.ai_consent_checkbox.blockSignals(False)

            # Reset avatar to default circular avatar
            self._set_circular_avatar(None) # Pass None to use default

            # Reset stats and clear achievements
            self.reset_stats() # This method also sets reg_date_label to N/A


    def load_stats(self):
        """Load and display user stats and achievements."""
        if not self.current_user:
            return

        user_id = self.current_user["id"] # Get user_id once

        # Get all user check-ins
        # check_ins = self.progress_tracker.get_all_user_check_ins(user_id) # Not directly needed for summary stats
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        self.total_label.setText(str(total_check_ins))

        # Calculate longest streak across all challenges
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(user_id)
        self.streak_label.setText(str(longest_streak))

        # Get subscribed challenges count
        challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(challenges)
        self.challenges_label.setText(str(subscribed_challenges_count))

        # Load dynamic achievements using the new method
        self.load_achievements()


    def reset_stats(self):
        """Reset stats and achievements, and clear profile fields on logout."""
        # Reset stats labels
        self.total_label.setText("0")
        self.streak_label.setText("0")
        self.challenges_label.setText("0")

        # Clear dynamic achievements
        self.clear_achievements()

        # Clear profile fields (remains the same)
        if self.username_label: self.username_label.setText("N/A")
        if self.avatar_label:
             self._set_circular_avatar(None) # Use helper with None for default
        if self.reg_date_label: self.reg_date_label.setText("N/A")
        if self.bio_display_label: self.bio_display_label.setText("请先登录")
        if self.bio_edit: self.bio_edit.setText("")
        self.toggle_bio_edit(edit_mode=False) # Ensure display mode

    # --- New Achievement Methods (Adapted from progress_ui.py) ---

    def load_achievements(self):
        """Load and display user achievements/badges within the scroll area."""
        if not self.current_user:
            self.clear_achievements() # Clear if no user
            return

        user_id = self.current_user["id"]

        # --- Fetch achievement data ---
        total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
        longest_streak = self.progress_tracker.get_longest_streak_all_challenges(user_id)
        subscribed_challenges = self.challenge_manager.get_user_challenges(user_id)
        subscribed_challenges_count = len(subscribed_challenges)
        # Fetch category counts if needed by achievements_data
        eco_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "环保")
        community_check_ins = self.progress_tracker.get_check_ins_count_by_category(user_id, "社区服务")

        # --- Define achievements_data (Mirrors progress_ui.py) ---
        achievements_data = [
            # Check-in Milestones
            {"name": "善行初学者", "target": 10, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善行践行者", "target": 50, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            {"name": "善意大师", "target": 100, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/award.svg"},
            # Streak Milestones
            {"name": "坚持不懈", "target": 7, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "毅力之星", "target": 14, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            {"name": "恒心典范", "target": 30, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/zap.svg"},
            # Subscription Milestones
            {"name": "探索之心", "target": 5, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "挑战收藏家", "target": 10, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            {"name": "领域专家", "target": 20, "current": subscribed_challenges_count, "unit": "个挑战", "icon": ":/icons/book-open.svg"},
            # Category Milestones
            {"name": "环保卫士", "target": 10, "current": eco_check_ins, "unit": "次环保行动", "icon": ":/icons/leaf.svg"},
            {"name": "社区之星", "target": 10, "current": community_check_ins, "unit": "次社区服务", "icon": ":/icons/users.svg"},
            # Generic Target Milestones
            {"name": "目标达成者", "target": 25, "current": total_check_ins, "unit": "次打卡", "icon": ":/icons/target.svg"},
            {"name": "闪耀新星", "target": 15, "current": longest_streak, "unit": "天连胜", "icon": ":/icons/star.svg"},
        ]

        # --- Clear previous achievements ---
        self.clear_achievements()

        achievements_added = False
        # --- Populate achievements layout ---
        for ach in achievements_data:
            # Only display achievements with a positive target
            if ach["target"] > 0:
                achievements_added = True
                ach_layout = QHBoxLayout()
                ach_layout.setSpacing(10)

                # Create a frame to contain the achievement item
                ach_frame = QFrame()
                ach_frame.setObjectName("achievement_frame")
                ach_frame.setFrameShape(QFrame.StyledPanel)
                ach_frame.setFrameShadow(QFrame.Raised)
                ach_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 允许水平扩展
                ach_frame.setStyleSheet("""
                    QFrame#achievement_frame {
                        border-radius: 12px;  /* 圆角 */
                        background-color: rgba(40, 40, 40, 0.7);  /* 背景色 */
                        padding: 10px;  /* 内边距 */
                        border: 1px solid rgba(80, 80, 80, 0.6);  /* 边框 */
                        margin: 2px;  /* 外边距 */
                    }
                """)

                # Use a horizontal layout for the frame content
                frame_layout = QHBoxLayout(ach_frame)
                frame_layout.setContentsMargins(12, 10, 12, 10)  # Increased margins
                frame_layout.setSpacing(15)  # Increased spacing

                # Icon Label
                icon_label = QLabel()
                icon_path = ach.get("icon", None)
                if icon_path:
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        pixmap = icon.pixmap(QSize(24, 24))
                        icon_label.setPixmap(pixmap)
                    else:
                        logging.warning(f"Failed to load achievement icon: {icon_path}")
                        icon_label.setText("?")
                        icon_label.setFixedSize(24, 24)
                        icon_label.setAlignment(Qt.AlignCenter)
                else:
                    # Keep space consistent even without icon
                    icon_label.setFixedSize(24, 24)

                icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                frame_layout.addWidget(icon_label)

                # Title and Progress in a vertical layout
                info_layout = QVBoxLayout()
                info_layout.setSpacing(4)

                # Title Label
                title_label = QLabel(ach["name"])
                title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #f5f5f5;")  # 更大的字体和更亮的颜色
                info_layout.addWidget(title_label)

                # Progress Bar
                progress_bar = QProgressBar()
                progress_bar.setRange(0, ach['target'])
                progress_bar.setFixedHeight(22)  # 更高的进度条
                progress_bar.setMinimumWidth(200)  # 更宽的最小宽度
                progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 允许水平扩展
                # 设置进度条样式
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        background-color: rgba(35, 35, 35, 0.9);
                        border-radius: 11px;
                        text-align: center;
                        color: white;
                        font-weight: bold;
                        font-size: 14px;
                        padding: 0px;
                        border: 1px solid rgba(80, 80, 80, 0.7);
                    }
                    QProgressBar::chunk {
                        background-color: #FF9800;
                        border-radius: 10px;
                    }
                """)
                display_value = min(ach['current'], ach['target'])
                progress_bar.setValue(display_value)
                progress_bar.setFormat(f"{display_value}/{ach['target']} {ach['unit']}")
                progress_bar.setAlignment(Qt.AlignCenter)

                # Styling with improved colors
                if ach["current"] >= ach["target"]:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #4CAF50;  /* Green */
                            border-radius: 10px;  /* Increased radius */
                        }
                        QProgressBar {
                            border: 1px solid #777;  /* Lighter border */
                            border-radius: 11px;  /* Increased radius */
                            text-align: center;
                            font-size: 14px;  /* Larger font */
                            background-color: #383838;  /* Slightly lighter background */
                            color: white;  /* White text */
                            padding: 1px;  /* Added padding */
                            font-weight: bold;
                        }
                    """)
                else:
                    progress_bar.setStyleSheet("""
                        QProgressBar::chunk {
                            background-color: #FF9800;  /* Warm orange */
                            border-radius: 10px;  /* Increased radius */
                        }
                        QProgressBar {
                            border: 1px solid #777;  /* Lighter border */
                            border-radius: 11px;  /* Increased radius */
                            text-align: center;
                            font-size: 14px;  /* Larger font */
                            background-color: #383838;  /* Slightly lighter background */
                            color: white;  /* White text */
                            padding: 1px;  /* Added padding */
                            font-weight: bold;
                        }
                    """)

                info_layout.addWidget(progress_bar)
                frame_layout.addLayout(info_layout)

                # Add the frame to the achievement layout
                ach_layout.addWidget(ach_frame)

                # Insert the new achievement layout *before* the spacer
                insert_index = self.achievements_layout.count() - 1 # Index before the spacer
                self.achievements_layout.insertLayout(insert_index, ach_layout)

        # --- Manage placeholder visibility ---
        if achievements_added:
            self.achievements_placeholder.hide()
            # Ensure spacer pushes content up
            self.achievements_spacer.changeSize(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            self.achievements_placeholder.setText("暂无成就，继续努力吧！")
            self.achievements_placeholder.show()
            # Collapse spacer if no achievements
            self.achievements_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)

    def clear_achievements(self):
        """Clear the achievements display area, keeping placeholder and spacer."""
        if not self.achievements_layout:
            return

        # Remove all items except the placeholder (index 0) and spacer (last index)
        # Iterate backwards to avoid index issues while removing
        layout_count = self.achievements_layout.count()
        if layout_count > 2: # If there are achievements added (more than placeholder + spacer)
            for i in range(layout_count - 2, 0, -1): # Iterate from second-to-last down to index 1
                item = self.achievements_layout.takeAt(i)
                if item:
                    # Remove layout
                    if item.layout():
                        # Recursively delete widgets within the layout
                        while item.layout().count():
                            child = item.layout().takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()
                        item.layout().deleteLater()
                    # Remove widget
                    elif item.widget():
                        item.widget().deleteLater()
                    # Remove spacer (shouldn't happen here, but good practice)
                    elif item.spacerItem():
                        pass # Don't delete the main spacer here
                    del item

        # Ensure placeholder is visible and spacer is collapsed after clearing
        if self.achievements_layout.count() == 2: # Should be placeholder + spacer
            placeholder_item = self.achievements_layout.itemAt(0)
            spacer_item = self.achievements_layout.itemAt(1)

            if placeholder_item and isinstance(placeholder_item.widget(), QLabel) and spacer_item and spacer_item.spacerItem():
                placeholder_item.widget().setText("暂无成就，继续努力吧！") # Reset text just in case
                placeholder_item.widget().show()
                # Collapse spacer when placeholder is shown
                spacer_item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
            else:
                 logging.warning("clear_achievements (profile): Layout structure incorrect after clearing.")
                 # Attempt to reset placeholder anyway
                 if self.achievements_placeholder:
                     self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                     self.achievements_placeholder.show()
                 # Try to find and collapse spacer
                 for i in range(self.achievements_layout.count()):
                     item = self.achievements_layout.itemAt(i)
                     if item and item.spacerItem():
                         item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
                         break
        elif self.achievements_layout.count() == 0: # Should not happen with placeholder/spacer logic
             logging.warning("clear_achievements (profile): Layout became empty, re-adding placeholder and spacer.")
             if self.achievements_placeholder and self.achievements_spacer:
                 self.achievements_layout.addWidget(self.achievements_placeholder)
                 self.achievements_layout.addSpacerItem(self.achievements_spacer)
                 self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                 self.achievements_placeholder.show()
                 self.achievements_spacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
        else: # Only placeholder or only spacer? Something is wrong.
             logging.warning(f"clear_achievements (profile): {self.achievements_layout.count()} items remain, expected 2.")
             # Ensure placeholder is visible
             if self.achievements_placeholder:
                 self.achievements_placeholder.setText("暂无成就，继续努力吧！")
                 self.achievements_placeholder.show()
             # Try to find and collapse spacer
             for i in range(self.achievements_layout.count()):
                 item = self.achievements_layout.itemAt(i)
                 if item and item.spacerItem():
                     item.spacerItem().changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
                     break


    # ... (show_password_dialog, update_user_info, logout remain the same) ...
    def show_password_dialog(self):
        """Show the password change dialog."""
        if not self.current_user:
            return

        dialog = PasswordDialog(self.user_manager, self.current_user, self)
        dialog.password_changed.connect(self.update_user_info)
        dialog.exec()

    def update_user_info(self, user_info):
        """
        Update user information in the application.

        Args:
            user_info (dict): Updated user information
        """
        self.current_user = user_info
        self.user_updated.emit(user_info)

    def logout(self):
        """Log out the current user."""
        # Ask for confirmation using AnimatedMessageBox
        reply = AnimatedMessageBox.showQuestion( # Use AnimatedMessageBox.showQuestion
            self,
            "退出登录",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_user = None
            self.reset_stats() # This now also clears achievements
            # Emit signal slightly delayed after confirmation
            QTimer.singleShot(10, self.user_logged_out.emit)


    # --- Bio Editing Methods (remain the same) ---
    @Slot() # Changed from @Slot(bool)
    def toggle_bio_edit(self, edit_mode=None):
        """Toggle between displaying and editing the bio."""
        # Use class-level logger instead of local variable
        if edit_mode is None:
            # Toggle based on current visibility of edit button
            edit_button_visible = self.edit_bio_button.isVisible()
            currently_editing = not edit_button_visible
            edit_mode = not currently_editing

        self.bio_display_label.setVisible(not edit_mode)
        self.edit_bio_button.setVisible(not edit_mode)

        self.bio_edit.setVisible(edit_mode)
        self.save_bio_button.setVisible(edit_mode)
        self.cancel_bio_button.setVisible(edit_mode)

        if not edit_mode: # If switching back to display mode
             # Reset edit text to current display text in case of cancel
             current_bio = self.bio_display_label.text()
             if current_bio == "这个人很神秘，什么也没留下..." or current_bio == "请先登录":
                 self.bio_edit.setText("")
             else:
                 self.bio_edit.setText(current_bio)
        else:
            # Optionally set focus to the editor when entering edit mode
            self.bio_edit.setFocus()

    @Slot()
    def save_bio(self):
        """Save the edited bio."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "用户未登录")
            return

        new_bio = self.bio_edit.toPlainText().strip()

        # --- Call backend to update profile ---
        success = self.user_manager.update_profile(self.current_user["id"], bio=new_bio)

        if success:
            # Update internal user data (important!)
            self.current_user["bio"] = new_bio
            # Update display label
            if new_bio:
                self.bio_display_label.setText(new_bio)
            else:
                self.bio_display_label.setText("这个人很神秘，什么也没留下...")

            # Switch back to display mode
            self.toggle_bio_edit(edit_mode=False)
            AnimatedMessageBox.showInformation(self, "成功", "个人简介已更新！")
            # Emit signal if needed
            self.user_updated.emit(self.current_user)
        else:
            AnimatedMessageBox.showWarning(self, "失败", "无法保存个人简介，请稍后重试。")

    # --- Avatar Change Method (remains the same) ---
    @Slot()
    def change_avatar(self):
        """Opens a file dialog, reads image data, saves blob to DB, and updates profile."""
        if not self.current_user:
            AnimatedMessageBox.showWarning(self, "错误", "请先登录")
            return

        # Open file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;All Files (*)")
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]

                try:
                    # Read image file into bytes
                    with open(source_path, 'rb') as f:
                        avatar_bytes = f.read()

                    # --- Optional: Image Resizing/Compression before saving ---
                    max_dimension = 256 # Example: Limit to 256x256
                    quality = 85 # JPEG quality if saving as JPG
                    save_format = "PNG" # Or "JPG"

                    temp_pixmap = QPixmap()
                    if temp_pixmap.loadFromData(avatar_bytes):
                        if temp_pixmap.width() > max_dimension or temp_pixmap.height() > max_dimension:
                            scaled_pixmap = temp_pixmap.scaled(max_dimension, max_dimension, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            byte_array = QByteArray()
                            buffer = QBuffer(byte_array)
                            buffer.open(QIODevice.WriteOnly)
                            # Save resized pixmap back to bytes
                            if save_format == "JPG":
                                scaled_pixmap.save(buffer, "JPG", quality)
                            else:
                                scaled_pixmap.save(buffer, "PNG") # PNG is lossless but might be larger
                            avatar_bytes = byte_array.data() # Get bytes from QByteArray
                            logging.info(f"Resized avatar to fit within {max_dimension}x{max_dimension} ({len(avatar_bytes)} bytes)") # Use logging
                        else:
                             logging.info(f"Avatar size is within limits ({len(avatar_bytes)} bytes)") # Use logging
                    else:
                        AnimatedMessageBox.showCritical(self, "错误", "无法加载所选图片数据。")
                        return
                    # --- End Optional Resizing ---

                    # Update database with blob data
                    success = self.user_manager.update_profile(
                        self.current_user["id"],
                        avatar_data=avatar_bytes # Pass the image bytes (potentially resized)
                    )

                    if success:
                        # Update internal user data
                        self.current_user["avatar"] = avatar_bytes
                        # Update the UI
                        self._set_circular_avatar(avatar_bytes)
                        AnimatedMessageBox.showInformation(self, "成功", "头像已更新！")
                        # Emit signal to notify other parts
                        self.user_updated.emit(self.current_user) # Pass updated user dict
                    else:
                        AnimatedMessageBox.showWarning(self, "失败", "无法更新数据库中的头像数据。")

                except FileNotFoundError:
                     AnimatedMessageBox.showCritical(self, "错误", f"无法找到文件: {source_path}")
                except Exception as e:
                    logging.error(f"Error changing avatar: {e}") # Use logging
                    AnimatedMessageBox.showCritical(self, "错误", f"更换头像时发生错误: {e}")

    @Slot()
    def request_delete_account(self):
        """Handle the request to delete the user account."""
        if not self.current_user:
            return

        username = self.current_user.get("username", "")

        # Step 1: Ask for password confirmation
        password, ok = QInputDialog.getText(
            self,
            "确认注销账号",
            f"请输入您的密码以确认注销账号 \"{username}\"：",
            QLineEdit.Password
        )

        if not ok or not password:
            # User cancelled or entered empty password
            return

        # Step 2: Show a critical confirmation dialog
        confirm_text = (
            f"您确定要永久注销账号 \"{username}\" 吗？\n\n"
            f"**此操作将删除您的所有个人信息、挑战订阅、打卡记录和提醒设置！**\n\n"
            f"**此操作不可恢复！**"
        )
        reply = AnimatedMessageBox.showCritical(
            self,
            "警告：永久删除账号",
            confirm_text,
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            # Step 3: Call backend to delete account
            try:
                success = self.user_manager.delete_user_account(self.current_user["id"], password)

                if success:
                    AnimatedMessageBox.showInformation(self, "账号已注销", f"账号 \"{username}\" 已被永久删除。")
                    # Trigger logout process to reset UI and go to login screen
                    QTimer.singleShot(10, self.user_logged_out.emit)
                else:
                    # Password might be incorrect, or other backend error
                    AnimatedMessageBox.showWarning(self, "注销失败", "密码不正确或发生内部错误，无法注销账号。")
            except Exception as e:
                logging.error(f"Error during account deletion for user {self.current_user['id']}: {e}")
                AnimatedMessageBox.showCritical(self, "注销出错", f"注销过程中发生意外错误：{e}")
