import logging
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap


class StatsAchievementsWidget(QWidget):
    """
    Widget for displaying user statistics and achievements.
    """

    def __init__(
        self,
        user_manager: Any,
        progress_tracker: Any,
        challenge_manager: Any,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.user_manager = user_manager
        self.progress_tracker = progress_tracker
        self.challenge_manager = challenge_manager
        self.current_user: Optional[Dict[str, Any]] = None

        # Initialize UI elements for stats and achievements
        self.total_label: QLabel = QLabel("0")
        self.streak_label: QLabel = QLabel("0")
        self.challenges_label: QLabel = QLabel("0")

        # Initialize achievements related widgets
        self.achievements_group: QGroupBox = QGroupBox("我的成就")
        self.achievements_scroll_area: QScrollArea = QScrollArea()
        self.achievements_container: QWidget = QWidget()
        self.achievements_layout: QGridLayout = QGridLayout(self.achievements_container)
        self.achievements_placeholder: QLabel = QLabel("暂无成就，继续努力吧！")
        self.achievements_spacer: QSpacerItem = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the statistics and achievements section."""
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # No margins for the main widget layout

        self.stats_group = QGroupBox("统计与成就")
        self.stats_group.setObjectName("stats_group")
        self.stats_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.stats_group.setMinimumWidth(400)

        stats_layout = QVBoxLayout(self.stats_group)
        stats_layout.setContentsMargins(15, 20, 15, 15)
        stats_layout.setSpacing(15)

        # --- Summary Section ---
        summary_group = QGroupBox("概览")
        summary_group.setObjectName("summary_group")
        summary_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(10)
        summary_layout.setContentsMargins(10, 15, 10, 15)

        # Create styled stat displays (Helper function)
        def create_stat_display(
            value: str, title: str, icon_path: str
        ) -> tuple[QFrame, QLabel]:
            frame = QFrame()
            frame.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            frame.setObjectName("stat_frame")

            stat_layout = QVBoxLayout(frame)
            stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.setContentsMargins(5, 5, 5, 5)
            stat_layout.setSpacing(6)

            if icon_path:
                icon_label = QLabel()
                icon_label.setObjectName("stat_icon_label")
                icon = QIcon(icon_path)
                if not icon.isNull():
                    pixmap = icon.pixmap(QSize(20, 20))
                    icon_label.setPixmap(pixmap)
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    stat_layout.addWidget(icon_label)

            value_label = QLabel(value)
            value_label.setObjectName("stat_value_label")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)

            title_label = QLabel(title)
            title_label.setObjectName("stat_title_label")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(title_label)

            return frame, value_label

        # Total check-ins
        total_frame, self.total_label = create_stat_display(
            "0", "总打卡次数", ":/icons/check-circle.svg"
        )
        summary_layout.addWidget(total_frame, 0, 0)

        # Longest streak
        streak_frame, self.streak_label = create_stat_display(
            "0", "最长连续打卡", ":/icons/zap.svg"
        )
        summary_layout.addWidget(streak_frame, 0, 1)

        # Challenges
        challenges_frame, self.challenges_label = create_stat_display(
            "0", "已订阅挑战", ":/icons/book-open.svg"
        )
        summary_layout.addWidget(challenges_frame, 0, 2)

        summary_layout.setColumnStretch(0, 1)
        summary_layout.setColumnStretch(1, 1)
        summary_layout.setColumnStretch(2, 1)

        stats_layout.addWidget(summary_group)

        # --- Achievements Section ---
        self.achievements_group = QGroupBox("我的成就")
        self.achievements_group.setObjectName("achievements_group")
        self.achievements_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.achievements_group.setMinimumHeight(300)

        achievements_group_layout = QVBoxLayout(self.achievements_group)
        achievements_group_layout.setContentsMargins(8, 15, 8, 8)
        achievements_group_layout.setSpacing(8)

        self.achievements_scroll_area = QScrollArea()
        self.achievements_scroll_area.setWidgetResizable(True)
        self.achievements_scroll_area.setObjectName("achievements_scroll_area")
        self.achievements_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.achievements_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.achievements_container = QWidget()
        self.achievements_container.setObjectName("achievements_container")
        self.achievements_scroll_area.setWidget(self.achievements_container)

        self.achievements_layout = QGridLayout(self.achievements_container)
        self.achievements_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.achievements_layout.setSpacing(4)
        self.achievements_layout.setContentsMargins(2, 2, 2, 2)

        self.achievements_placeholder = QLabel("暂无成就，继续努力吧！")
        self.achievements_placeholder.setObjectName("achievements_placeholder")
        self.achievements_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.achievements_layout.addWidget(self.achievements_placeholder, 0, 0, 1, 3)

        # Add spacer at the end of the grid layout
        self.achievements_spacer = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.achievements_layout.addItem(self.achievements_spacer, 100, 0, 1, 3)

        achievements_group_layout.addWidget(self.achievements_scroll_area)
        stats_layout.addWidget(self.achievements_group)

        # Add the main stats group to the widget's layout
        main_layout.addWidget(self.stats_group)

    @Slot(dict)
    def set_user(self, user: Optional[Dict[str, Any]]) -> None:
        """Sets the current user and loads their stats and achievements."""
        self.current_user = user
        if user:
            self.load_stats()
        else:
            self.reset_stats()

    def load_stats(self) -> None:
        """Load and display user stats and achievements."""
        if not self.current_user:
            self.reset_stats()
            return

        user_id = self.current_user.get("id")
        if not user_id:
            self.reset_stats()
            return

        try:
            total_check_ins = self.progress_tracker.get_total_check_ins(user_id)
            self.total_label.setText(str(total_check_ins))

            longest_streak = self.progress_tracker.get_longest_streak_all_challenges(
                user_id
            )
            self.streak_label.setText(str(longest_streak))

            challenges = self.challenge_manager.get_user_challenges(user_id)
            subscribed_challenges_count = len(challenges)
            self.challenges_label.setText(str(subscribed_challenges_count))

            self.load_achievements()
        except Exception as e:
            logging.error(f"Error loading stats for user {user_id}: {e}")
            self.reset_stats()  # Reset on error

    def reset_stats(self) -> None:
        """Reset stats and achievements display."""
        self.total_label.setText("0")
        self.streak_label.setText("0")
        self.challenges_label.setText("0")
        self.clear_achievements()

    def load_achievements(self) -> None:
        """Load and display user achievements/badges within the scroll area."""
        if not self.current_user:
            self.clear_achievements()
            return

        user_id = self.current_user.get("id")
        if not user_id:
            self.clear_achievements()
            return

        try:
            # Fetch necessary data
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

            # Define achievements data
            achievements_data: List[Dict[str, Any]] = [
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
                },
                {
                    "name": "目标达成者",
                    "target": 25,
                    "current": total_check_ins,
                    "unit": "次打卡",
                    "icon": ":/icons/target.svg",
                },
                {
                    "name": "闪耀新星",
                    "target": 15,
                    "current": longest_streak,
                    "unit": "天连胜",
                    "icon": ":/icons/star.svg",
                },
            ]

            self.clear_achievements()  # Clear previous items

            achievements_added = False
            achievements_added_list: List[QFrame] = (
                []
            )  # List to track added achievements for grid layout
            for ach in achievements_data:
                if ach["target"] > 0:
                    achievements_added = True
                    ach_frame = QFrame()
                    ach_frame.setObjectName("achievement_frame")
                    ach_frame.setFrameShape(QFrame.Shape.StyledPanel)
                    ach_frame.setFrameShadow(QFrame.Shadow.Raised)
                    ach_frame.setSizePolicy(
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                    )

                    frame_layout = QHBoxLayout(ach_frame)
                    frame_layout.setContentsMargins(5, 4, 5, 4)
                    frame_layout.setSpacing(6)

                    # Icon Label
                    icon_label = QLabel()
                    icon_label.setObjectName("achievement_icon_label")
                    icon_path = ach.get("icon")
                    if icon_path:
                        icon = QIcon(icon_path)
                        if not icon.isNull():
                            pixmap = icon.pixmap(QSize(20, 20))
                            icon_label.setPixmap(pixmap)
                        else:
                            logging.warning(
                                f"Failed to load achievement icon: {icon_path}"
                            )
                            icon_label.setText("?")  # Placeholder if icon fails
                            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        icon_label.setText("")  # Empty label if no icon

                    icon_label.setFixedSize(QSize(24, 24))
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    frame_layout.addWidget(icon_label)

                    # Text content layout
                    text_layout = QVBoxLayout()
                    text_layout.setSpacing(2)

                    # Achievement Name - slightly smaller font
                    name_label = QLabel(ach["name"])
                    name_label.setObjectName("achievement_name_label")
                    text_layout.addWidget(name_label)

                    # Progress Text - slightly smaller font
                    progress_text = f"{ach['current']} / {ach['target']} {ach['unit']}"
                    progress_label = QLabel(progress_text)
                    progress_label.setObjectName("achievement_progress_label")
                    text_layout.addWidget(progress_label)

                    frame_layout.addLayout(text_layout)
                    frame_layout.addStretch()

                    # Add the frame to the achievements layout in a grid
                    row = len(achievements_added_list) // 3
                    col = len(achievements_added_list) % 3
                    self.achievements_layout.addWidget(ach_frame, row, col)
                    achievements_added_list.append(ach_frame)

            # Show/hide placeholder
            self.achievements_placeholder.setVisible(not achievements_added)

        except Exception as e:
            logging.error(f"Error loading achievements for user {user_id}: {e}")
            self.clear_achievements()  # Clear on error

    def clear_achievements(self) -> None:
        """Clears all achievement items from the layout."""
        if not self.achievements_layout:
            return

        # Remove all widgets from the grid layout
        while self.achievements_layout.count() > 0:
            item = self.achievements_layout.takeAt(0)
            if (
                item
                and item.widget()
                and item.widget() != self.achievements_placeholder
            ):
                item.widget().deleteLater()

        # Re-add the placeholder to the grid layout
        if (
            self.achievements_placeholder
            and self.achievements_layout.indexOf(self.achievements_placeholder) == -1
        ):
            self.achievements_layout.addWidget(
                self.achievements_placeholder, 0, 0, 1, 3
            )

        # Ensure placeholder is visible after clearing
        if self.achievements_placeholder:
            self.achievements_placeholder.setVisible(True)
