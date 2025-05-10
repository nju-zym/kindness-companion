# TODO: 实现社区善意墙展示界面 ([可选])

import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QFrame,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon
from .widgets.animated_message_box import AnimatedMessageBox
from ..backend.sync_manager import SyncManager


class CommunityWidget(QWidget):
    """
    Widget for displaying and managing the kindness wall.
    """

    def __init__(self, wall_manager, user_manager):
        """
        Initialize the community widget.

        Args:
            wall_manager: Wall manager instance
            user_manager: User manager instance
        """
        super().__init__()
        self.wall_manager = wall_manager
        self.user_manager = user_manager
        self.current_user = None
        self.sync_manager = SyncManager(wall_manager.db_manager)  # Add sync manager
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)

        # Add sync buttons
        self.create_sync_buttons()

        # Create post area
        self.create_post_area()

        # Create posts display area
        self.create_posts_area()

        # Load initial posts
        self.load_posts()

    def create_sync_buttons(self):
        """Create synchronization buttons."""
        sync_layout = QHBoxLayout()

        # Export button
        export_btn = QPushButton("导出数据")
        export_btn.setIcon(QIcon(":/icons/export.png"))
        export_btn.clicked.connect(self.export_data)
        sync_layout.addWidget(export_btn)

        # Import button
        import_btn = QPushButton("导入数据")
        import_btn.setIcon(QIcon(":/icons/import.png"))
        import_btn.clicked.connect(self.import_data)
        sync_layout.addWidget(import_btn)

        # Stats button
        stats_btn = QPushButton("同步统计")
        stats_btn.setIcon(QIcon(":/icons/stats.png"))
        stats_btn.clicked.connect(self.show_sync_stats)
        sync_layout.addWidget(stats_btn)

        sync_layout.addStretch()
        self.main_layout.addLayout(sync_layout)

    def create_post_area(self):
        """Create the area for creating new posts."""
        post_frame = QFrame()
        post_frame.setObjectName("post_frame")
        post_layout = QVBoxLayout(post_frame)
        post_layout.setSpacing(15)

        # Post content input
        self.post_content = QTextEdit()
        self.post_content.setPlaceholderText("分享你的善行故事...")
        self.post_content.setMaximumHeight(100)
        post_layout.addWidget(self.post_content)

        # Image preview and upload button
        image_layout = QHBoxLayout()

        self.image_preview = QLabel()
        self.image_preview.setFixedSize(100, 100)
        self.image_preview.setStyleSheet("border: 1px dashed #ccc;")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setText("图片预览")
        image_layout.addWidget(self.image_preview)

        button_layout = QVBoxLayout()

        self.upload_button = QPushButton("上传图片")
        self.upload_button.clicked.connect(self.upload_image)
        button_layout.addWidget(self.upload_button)

        self.remove_image_button = QPushButton("移除图片")
        self.remove_image_button.clicked.connect(self.remove_image)
        self.remove_image_button.setEnabled(False)
        button_layout.addWidget(self.remove_image_button)

        image_layout.addLayout(button_layout)
        image_layout.addStretch()
        post_layout.addLayout(image_layout)

        # Anonymous checkbox and post button
        bottom_layout = QHBoxLayout()

        self.anonymous_checkbox = QCheckBox("匿名发布")
        bottom_layout.addWidget(self.anonymous_checkbox)

        bottom_layout.addStretch()

        self.post_button = QPushButton("发布")
        self.post_button.clicked.connect(self.create_post)
        bottom_layout.addWidget(self.post_button)

        post_layout.addLayout(bottom_layout)

        self.main_layout.addWidget(post_frame)

    def create_posts_area(self):
        """Create the area for displaying posts."""
        # Create scroll area for posts
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create container widget for posts
        self.posts_container = QWidget()
        self.posts_layout = QVBoxLayout(self.posts_container)
        self.posts_layout.setSpacing(20)
        self.posts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.posts_container)
        self.main_layout.addWidget(self.scroll_area)

    def upload_image(self):
        """Handle image upload."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_name:
            try:
                # Load and display image
                pixmap = QPixmap(file_name)
                scaled_pixmap = pixmap.scaled(
                    100,
                    100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_preview.setPixmap(scaled_pixmap)
                self.image_preview.setScaledContents(True)
                self.remove_image_button.setEnabled(True)

                # Store image data
                with open(file_name, "rb") as f:
                    self.current_image_data = f.read()
            except Exception as e:
                logging.error(f"Error loading image: {e}")
                AnimatedMessageBox.critical(self, "错误", "无法加载图片，请重试。")

    def remove_image(self):
        """Remove the current image."""
        self.image_preview.clear()
        self.image_preview.setText("图片预览")
        self.remove_image_button.setEnabled(False)
        self.current_image_data = None

    def create_post(self):
        """Create a new post."""
        if not self.current_user:
            AnimatedMessageBox.warning(self, "提示", "请先登录后再发布内容。")
            return

        content = self.post_content.toPlainText().strip()
        if not content:
            AnimatedMessageBox.warning(self, "提示", "请输入发布内容。")
            return

        try:
            user_id = self.current_user.get(
                "id"
            )  # Use get() method to safely access id
            if not user_id:
                raise ValueError("Invalid user ID")

            post_id = self.wall_manager.create_post(
                user_id,
                content,
                (
                    self.current_image_data
                    if hasattr(self, "current_image_data")
                    else None
                ),
                self.anonymous_checkbox.isChecked(),
            )

            if post_id:
                # Clear input
                self.post_content.clear()
                self.remove_image()
                self.anonymous_checkbox.setChecked(False)

                # Reload posts
                self.load_posts()

                AnimatedMessageBox.information(self, "成功", "发布成功！")
            else:
                AnimatedMessageBox.critical(self, "错误", "发布失败，请重试。")
        except Exception as e:
            logging.error(f"Error creating post: {e}")
            AnimatedMessageBox.critical(self, "错误", "发布失败，请重试。")

    def load_posts(self):
        """Load and display posts."""
        # Clear existing posts
        while self.posts_layout.count():
            item = self.posts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            posts = self.wall_manager.get_posts()

            for post in posts:
                post_widget = self.create_post_widget(post)
                self.posts_layout.addWidget(post_widget)

            # Add stretch to push posts to the top
            self.posts_layout.addStretch()
        except Exception as e:
            logging.error(f"Error loading posts: {e}")
            AnimatedMessageBox.critical(self, "错误", "加载内容失败，请重试。")

    def create_post_widget(self, post):
        """Create a widget for displaying a post."""
        post_frame = QFrame()
        post_frame.setObjectName("post_frame")
        post_layout = QVBoxLayout(post_frame)
        post_layout.setSpacing(10)

        # Header with user info and timestamp
        header_layout = QHBoxLayout()

        # User avatar
        avatar_label = QLabel()
        if post.get("avatar"):
            pixmap = QPixmap()
            pixmap.loadFromData(post["avatar"])
            avatar_label.setPixmap(
                pixmap.scaled(
                    40,
                    40,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            avatar_label.setText("👤")
            avatar_label.setStyleSheet("font-size: 24px;")
        avatar_label.setFixedSize(40, 40)
        header_layout.addWidget(avatar_label)

        # User name and timestamp
        info_layout = QVBoxLayout()
        name_label = QLabel(post.get("display_name", "匿名用户"))
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        timestamp_label = QLabel(post.get("created_at", ""))
        timestamp_label.setStyleSheet("color: gray; font-size: 12px;")
        info_layout.addWidget(timestamp_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Delete button for own posts
        if self.current_user and post.get("user_id") == self.current_user.get("id"):
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda: self.delete_post(post["id"]))
            header_layout.addWidget(delete_button)

        post_layout.addLayout(header_layout)

        # Post content
        content_label = QLabel(post.get("content", ""))
        content_label.setWordWrap(True)
        post_layout.addWidget(content_label)

        # Post image if exists
        if post.get("image_data"):
            image_label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(post["image_data"])
            scaled_pixmap = pixmap.scaled(
                400,
                400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            post_layout.addWidget(image_label)

        # Like button and count
        footer_layout = QHBoxLayout()

        like_button = QPushButton("❤️")
        like_button.setCheckable(True)
        like_button.clicked.connect(lambda: self.toggle_like(post["id"]))
        footer_layout.addWidget(like_button)

        likes_label = QLabel(str(post.get("likes", 0)))
        footer_layout.addWidget(likes_label)

        footer_layout.addStretch()
        post_layout.addLayout(footer_layout)

        return post_frame

    def delete_post(self, post_id):
        """Delete a post."""
        if not self.current_user:
            AnimatedMessageBox.warning(self, "提示", "请先登录后再删除内容。")
            return

        try:
            user_id = self.current_user.get(
                "id"
            )  # Use get() method to safely access id
            if not user_id:
                raise ValueError("Invalid user ID")

            if self.wall_manager.delete_post(post_id, user_id):
                self.load_posts()
                AnimatedMessageBox.information(self, "成功", "删除成功！")
            else:
                AnimatedMessageBox.critical(self, "错误", "删除失败，请重试。")
        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            AnimatedMessageBox.critical(self, "错误", "删除失败，请重试。")

    def toggle_like(self, post_id):
        """Toggle like status for a post."""
        if not self.current_user:
            AnimatedMessageBox.warning(self, "提示", "请先登录后再点赞。")
            return

        try:
            user_id = self.current_user.get(
                "id"
            )  # Use get() method to safely access id
            if not user_id:
                raise ValueError("Invalid user ID")

            if self.wall_manager.like_post(post_id, user_id):
                self.load_posts()
            else:
                if self.wall_manager.unlike_post(post_id, user_id):
                    self.load_posts()
        except Exception as e:
            logging.error(f"Error toggling like: {e}")
            AnimatedMessageBox.critical(self, "错误", "操作失败，请重试。")

    def set_user(self, user):
        """Set the current user."""
        self.current_user = user
        if user is not None:  # Add check for None
            self.load_posts()  # Reload posts when user changes

    def export_data(self):
        """Export wall data to a JSON file."""
        if not self.current_user:
            AnimatedMessageBox.warning(self, "提示", "请先登录后再导出数据。")
            return

        try:
            export_file = self.sync_manager.export_data()
            if export_file:
                AnimatedMessageBox.information(
                    self,
                    "导出成功",
                    f"数据已导出到：\n{export_file}\n\n您可以通过以下方式分享：\n"
                    "1. 发送邮件\n"
                    "2. 上传到云存储\n"
                    "3. 通过即时通讯软件发送",
                )
            else:
                raise Exception("导出失败")
        except Exception as e:
            AnimatedMessageBox.critical(
                self, "导出失败", f"导出数据时发生错误：{str(e)}"
            )

    def import_data(self):
        """Import wall data from a JSON file."""
        if not self.current_user:
            AnimatedMessageBox.warning(self, "提示", "请先登录后再导入数据。")
            return

        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择导入文件", self.sync_manager.sync_dir, "JSON Files (*.json)"
            )

            if file_path:
                success, stats = self.sync_manager.import_data(file_path)
                if success:
                    message = (
                        f"导入完成！\n\n"
                        f"总计：{stats['total']} 条\n"
                        f"已导入：{stats['imported']} 条\n"
                        f"已跳过：{stats['skipped']} 条\n"
                        f"冲突：{stats['conflicts']} 条"
                    )
                    AnimatedMessageBox.information(self, "导入成功", message)
                    self.load_posts()  # Reload posts after import
                else:
                    raise Exception("导入失败")
        except Exception as e:
            AnimatedMessageBox.critical(
                self, "导入失败", f"导入数据时发生错误：{str(e)}"
            )

    def show_sync_stats(self):
        """Show synchronization statistics."""
        try:
            stats = self.sync_manager.get_sync_stats()
            if stats:
                message = (
                    f"同步统计：\n\n"
                    f"总帖子数：{stats['total_posts']}\n"
                    f"总点赞数：{stats['total_likes']}\n"
                    f"最新帖子：{stats['latest_post'] or '无'}"
                )
                AnimatedMessageBox.information(self, "同步统计", message)
            else:
                raise Exception("获取统计信息失败")
        except Exception as e:
            AnimatedMessageBox.critical(
                self, "统计失败", f"获取统计信息时发生错误：{str(e)}"
            )
