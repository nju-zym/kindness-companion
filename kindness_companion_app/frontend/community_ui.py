# TODO: 实现社区善意墙展示界面 ([可选])

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QPushButton
from PySide6.QtCore import Slot
from .widgets.animated_message_box import AnimatedMessageBox
import requests

class CommunityWidget(QWidget):
    """
    Widget for displaying the anonymous community kindness wall (optional feature).
    """
    def __init__(self):
        """Initialize the community widget."""
        super().__init__()
        self.current_user = None # Store user if needed for context, even if wall is anonymous

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        self.main_layout = QVBoxLayout(self)
        self.title_label = QLabel("善意墙 (社区分享)")
        self.title_label.setObjectName("title_label")
        self.main_layout.addWidget(self.title_label)

        # Placeholder for community wall content
        self.placeholder_label = QLabel("社区分享内容将在此处展示 (可选功能)。")
        self.main_layout.addWidget(self.placeholder_label)

        # TODO: Implement Anonymous Kindness Wall UI (Future Enhancement as per README)
        # This involves:
        # 1. Adding UI elements: Text input for new posts, button to submit, area to display posts.
        # 2. Fetching posts from the self-hosted API (GET /api/community/wall).
        # 3. Displaying fetched posts (handle pagination).
        # 4. Sending new posts to the API (POST /api/community/wall).
        # 5. Handling API errors gracefully.

        # Placeholder UI elements (add actual widgets)
        self.post_input = QTextEdit() # Example input
        self.post_input.setPlaceholderText("分享你的匿名善意...")
        self.submit_button = QPushButton("发布")
        self.posts_display_area = QScrollArea() # Example display area
        self.posts_widget = QWidget()
        self.posts_layout = QVBoxLayout(self.posts_widget)
        self.posts_display_area.setWidget(self.posts_widget)
        self.posts_display_area.setWidgetResizable(True)

        # Add placeholders to layout
        self.main_layout.addWidget(QLabel("匿名善意墙 (开发中)"))
        self.main_layout.addWidget(self.post_input)
        self.main_layout.addWidget(self.submit_button)
        self.main_layout.addWidget(self.posts_display_area)

        # Connect signals (placeholder)
        self.submit_button.clicked.connect(self.submit_new_post)

        # Initial load (placeholder)
        # self.load_posts()

    @Slot(dict)
    def set_user(self, user):
        """
        Set the current user.

        Args:
            user (dict): User information or None if logged out.
        """
        self.current_user = user
        if user:
            # Potentially load community data or enable features based on user state
            self.load_community_feed()
        else:
            # Clear community feed or disable interactions
            pass # Add clearing logic later

    def load_community_feed(self):
        """Load the community feed data (if implemented)."""
        # TODO: Implement API call and display logic
        print("Loading community feed...") # Placeholder

    # TODO: Add function to load posts from the API
    def load_posts(self, page=1, limit=10):
        """Fetches posts from the API and updates the display."""
        print(f"Loading posts: page={page}, limit={limit}") # Placeholder
        try:
            # response = requests.get(f"http://127.0.0.1:5000/api/community/wall?page={page}&limit={limit}")
            # response.raise_for_status()
            # data = response.json()
            # posts = data.get("posts", [])
            # Dummy data:
            posts = [
                {"id": 1, "message": "今天帮助了迷路的老奶奶。", "timestamp": "2025-05-03T10:00:00Z"},
                {"id": 2, "message": "给同事带了杯咖啡。", "timestamp": "2025-05-03T09:30:00Z"},
            ]
            self.display_posts(posts)
        except Exception as e:
            print(f"Error loading posts: {e}")
            # Show error message to user

    # TODO: Add function to display posts in the UI
    def display_posts(self, posts: list):
        """Clears and displays the fetched posts."""
        # Clear existing posts
        while self.posts_layout.count():
            item = self.posts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new posts
        if not posts:
            self.posts_layout.addWidget(QLabel("还没有人分享善意，快来做第一个吧！"))
        else:
            for post in posts:
                post_label = QLabel(f"{post['message']}\n<small><i>{post.get('timestamp', '')}</i></small>")
                post_label.setWordWrap(True)
                post_label.setStyleSheet("QLabel { border: 1px solid #eee; padding: 5px; margin-bottom: 5px; }")
                self.posts_layout.addWidget(post_label)
        self.posts_layout.addStretch()

    # TODO: Add function to submit a new post to the API
    def submit_new_post(self):
        """Submits the text from the input field to the API."""
        message = self.post_input.toPlainText().strip()
        if not message:
            # Show error: message cannot be empty
            AnimatedMessageBox.showWarning(self, "错误", "分享内容不能为空！")
            return

        print(f"Submitting post: {message}") # Placeholder
        try:
            # response = requests.post("http://127.0.0.1:5000/api/community/wall", json={"message": message})
            # response.raise_for_status()
            # data = response.json()
            # if data.get("success"):
            AnimatedMessageBox.showInfo(self, "成功", "您的善意已成功分享！")
            self.post_input.clear()
            # self.load_posts() # Refresh posts
            # else:
            #     AnimatedMessageBox.showCritical(self, "错误", f"分享失败: {data.get('error', '未知错误')}")
        except Exception as e:
            print(f"Error submitting post: {e}")
            AnimatedMessageBox.showCritical(self, "错误", f"分享失败: {e}")
