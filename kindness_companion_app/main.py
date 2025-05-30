import sys
import os
import platform
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (
    QIcon,
    QFont,
    QFontDatabase,
    QScreen,
    QStyleHints,
)  # Add QStyleHints
from PySide6.QtCore import (
    QFile,
    QTextStream,
    QDir,
    QOperatingSystemVersion,
    Qt,
    QEvent,
    QPoint,
    QObject,
    QIODevice,
    Signal,
)

from kindness_companion_app.frontend.main_window import MainWindow
from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.user_manager import UserManager
from kindness_companion_app.backend.challenge_manager import ChallengeManager
from kindness_companion_app.backend.progress_tracker import ProgressTracker
from kindness_companion_app.backend.reminder_scheduler import ReminderScheduler
from kindness_companion_app.backend.wall_manager import WallManager
from kindness_companion_app.backend.sync_manager import SyncManager
from kindness_companion_app.backend.utils import setup_logging
import kindness_companion_app.resources.resources_rc  # Import the compiled resources


def load_fonts():
    """Loads custom fonts from resources."""
    font_dir_path = ":/fonts/"  # Use the resource path prefix
    fonts_loaded = []
    font_files = [
        "Hiragino Sans GB.ttc",
        "Songti.ttc",
        "STHeiti Light.ttc",
        "STHeiti Medium.ttc",
    ]

    logging.info(f"Attempting to load fonts from resource path: {font_dir_path}")

    for font_file in font_files:
        # Construct the full resource path for each font using the alias
        resource_font_path = (
            f"{font_dir_path}{font_file}"  # Path uses the alias directly
        )
        logging.debug(f"Attempting to load font from resource: {resource_font_path}")

        font_id = QFontDatabase.addApplicationFont(resource_font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                # Log all families associated with the font file (TTC might have multiple)
                for family in families:
                    if (
                        family not in fonts_loaded
                    ):  # Avoid duplicates if TTC lists variations
                        fonts_loaded.append(family)
                    logging.info(
                        f"Successfully loaded font family: {family} from {resource_font_path}"
                    )
            else:
                logging.warning(
                    f"Loaded font from {resource_font_path} but could not retrieve family names (ID: {font_id})."
                )
        else:
            logging.warning(
                f"Failed to load font from resource: {resource_font_path}. Check path and QRC compilation."
            )
            # Keep the development path check as a fallback if needed, but prioritize resources
            dev_font_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "resources", "fonts", font_file)
            )
            if os.path.exists(dev_font_path):
                logging.info(f"Attempting fallback load from dev path: {dev_font_path}")
                font_id_dev = QFontDatabase.addApplicationFont(dev_font_path)
                if font_id_dev != -1:
                    families_dev = QFontDatabase.applicationFontFamilies(font_id_dev)
                    if families_dev:
                        for family_dev in families_dev:
                            if family_dev not in fonts_loaded:
                                fonts_loaded.append(family_dev)
                            logging.info(
                                f"Successfully loaded font family (dev path): {family_dev} from {dev_font_path}"
                            )
                    else:
                        logging.warning(
                            f"Loaded font from dev path {dev_font_path} but could not retrieve family names (ID: {font_id_dev})."
                        )
                else:
                    logging.warning(f"Failed to load font (dev path): {dev_font_path}")

    if not fonts_loaded:
        logging.error("No custom fonts were loaded successfully!")
    else:
        # Log all available families after attempting to load all fonts
        logging.info(
            f"Available application font families after loading: {QFontDatabase.families()}"
        )

    return list(set(fonts_loaded))  # Return unique list


class ThemeManager(QObject):
    """管理应用主题的类，支持系统主题变化的检测和自动切换"""

    # 主题变更信号
    theme_changed = Signal(str, str)  # 参数: theme_type, theme_style

    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self.logger = logger
        # 启动时自动检测系统主题
        self.system_theme = self.detect_system_theme()
        self.current_theme = self.system_theme  # 启动时跟随系统
        self.theme_style = (
            "standard"  # 默认使用Standard主题样式, 可选: "warm", "standard", "sourcio"
        )
        self.follow_system = False  # 启动后只允许手动切换

        # 创建系统主题变化监听器
        self.app.installEventFilter(self)

        # 初始检测系统主题
        self.logger.info(f"初始系统主题检测: {self.system_theme}")

    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获系统主题变化事件"""
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.logger.info("检测到系统主题变化")
            # 重新检测系统主题
            new_system_theme = self.detect_system_theme()
            if new_system_theme != self.system_theme:
                self.system_theme = new_system_theme
                self.logger.info(f"系统主题已变更为: {self.system_theme}")
                # 如果设置为跟随系统主题，则应用新主题
                if self.follow_system:
                    self.current_theme = self.system_theme
                    self.apply_theme()

        # 继续传递事件
        return super().eventFilter(obj, event)

    def detect_system_theme(self):
        """检测系统主题，返回 'light' 或 'dark'"""
        # Preferred method: Use QStyleHints for Qt 6.5+
        try:
            hints = self.app.styleHints()
            color_scheme = hints.colorScheme()
            if color_scheme == Qt.ColorScheme.Light:
                self.logger.info("检测到系统使用浅色主题 (QStyleHints)")
                return "light"
            elif color_scheme == Qt.ColorScheme.Dark:
                self.logger.info("检测到系统使用深色主题 (QStyleHints)")
                return "dark"
            else:  # Qt.ColorScheme.Unknown or other values
                self.logger.warning(
                    f"QStyleHints 返回未知颜色方案: {color_scheme}. 回退到亮度检测."
                )
        except AttributeError:
            # colorScheme might not be available in older Qt versions
            self.logger.warning("QStyleHints.colorScheme() 不可用. 回退到亮度检测.")
        except Exception as e:
            self.logger.error(f"检测 QStyleHints 时出错: {e}. 回退到亮度检测.")

        # Fallback method: Use palette brightness
        self.logger.info("使用调色板亮度检测系统主题...")
        app_palette = self.app.palette()
        # 获取窗口背景色
        window_color = app_palette.color(app_palette.ColorRole.Window)
        # 计算亮度 (0.0-1.0)，使用标准RGB亮度公式 (浮点数版本)
        brightness = (
            0.299 * window_color.redF()
            + 0.587 * window_color.greenF()
            + 0.114 * window_color.blueF()
        )

        # 使用 0.5 作为阈值
        threshold = 0.5
        if brightness >= threshold:
            self.logger.info(f"检测到系统使用浅色主题 (亮度: {brightness:.3f})")
            return "light"
        else:
            self.logger.info(f"检测到系统使用深色主题 (亮度: {brightness:.3f})")
            return "dark"

    def apply_theme(self):
        """应用当前主题，只加载融合后的 sourcio_light.qss 或 sourcio_dark.qss，并刷新顶层窗口（提升切换速度）"""
        style_file_name = f"sourcio_{self.current_theme}.qss"
        style_file_path = f":/styles/{style_file_name}"
        style_file = QFile(style_file_path)
        if style_file.open(
            QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text
        ):
            stream = QTextStream(style_file)
            self.app.setStyleSheet(stream.readAll())
            style_file.close()
            # 只刷新顶层窗口，提升切换速度
            for widget in self.app.topLevelWidgets():
                widget.setStyle(self.app.style())
                widget.update()
            # 预留：切换主题相关的图片/图标
            self.update_theme_icons()
            # 发出主题变更信号
            self.theme_changed.emit(self.current_theme, self.theme_style)

    def update_theme_icons(self):
        # 预留：根据 self.current_theme 切换所有需要的图标/图片资源
        pass


def main():
    print("DEBUG: Starting main function...")
    # 检查命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="Kindness Companion App")
    parser.add_argument(
        "--reset-login", action="store_true", help="清除登录状态，显示登录界面"
    )
    args = parser.parse_args()

    # 创建应用程序实例
    print("DEBUG: Creating QApplication...")
    app = QApplication(sys.argv)
    print("DEBUG: QApplication created.")

    # 设置日志记录
    print("DEBUG: Setting up logging...")
    logger = setup_logging()
    print("DEBUG: Logging setup complete.")

    # 创建主题管理器并初始化
    print("DEBUG: Creating ThemeManager...")
    theme_manager = ThemeManager(app, logger)
    print("DEBUG: ThemeManager created.")
    # 设置 theme_style 为 "standard" 作为默认启动主题
    theme_manager.theme_style = "standard"

    # 将主题管理器存储在应用程序实例中，使其可以被其他组件访问
    app.setProperty("theme_manager", theme_manager)
    # 确保主题管理器可以被全局访问
    app.setProperty("global_theme_manager", theme_manager)

    print("DEBUG: Applying theme...")
    theme_manager.apply_theme()  # Re-apply after changing style if needed for testing
    print("DEBUG: Theme applied.")

    # Initialize backend managers
    print("DEBUG: Initializing DatabaseManager...")
    db_manager = DatabaseManager()
    print("DEBUG: DatabaseManager initialized.")
    print("DEBUG: Initializing UserManager...")
    user_manager = UserManager(db_manager)
    print("DEBUG: UserManager initialized.")

    # 如果指定了重置登录参数，清除登录状态
    if args.reset_login:
        print("DEBUG: Clearing login state as requested...")
        user_manager.clear_login_state()
        print("DEBUG: Login state cleared.")
    print("DEBUG: Initializing ChallengeManager...")
    challenge_manager = ChallengeManager(db_manager)
    print("DEBUG: ChallengeManager initialized.")
    print("DEBUG: Initializing ProgressTracker...")
    progress_tracker = ProgressTracker(db_manager)
    print("DEBUG: ProgressTracker initialized.")
    print("DEBUG: Initializing ReminderScheduler...")
    reminder_scheduler = ReminderScheduler(db_manager)
    print("DEBUG: ReminderScheduler initialized.")
    print("DEBUG: Initializing WallManager...")
    wall_manager = WallManager(db_manager)
    print("DEBUG: WallManager initialized.")
    print("DEBUG: Initializing SyncManager...")
    sync_manager = SyncManager(db_manager)
    print("DEBUG: SyncManager initialized.")

    # Initialize sync for all existing users
    print("DEBUG: Initializing sync for existing users...")
    try:
        initialized_count = sync_manager.initialize_all_users_sync()
        print(f"DEBUG: Initialized sync for {initialized_count} users.")
    except Exception as e:
        print(f"DEBUG: Error initializing user sync: {e}")

    # Initialize enhanced dialogue generator
    try:
        print("DEBUG: Initializing Enhanced Dialogue Generator...")
        from kindness_companion_app.ai_core.pet_handler import (
            initialize_enhanced_dialogue,
        )

        if initialize_enhanced_dialogue:
            initialize_enhanced_dialogue(db_manager)
            print("DEBUG: Enhanced Dialogue Generator initialized.")
        else:
            print("DEBUG: initialize_enhanced_dialogue function not available.")
    except ImportError as e:
        print(f"DEBUG: Could not import initialize_enhanced_dialogue: {e}")
    except Exception as e:
        print(f"DEBUG: Error initializing Enhanced Dialogue Generator: {e}")

    # 创建主窗口，并传入管理器实例
    print("DEBUG: Creating MainWindow...")
    main_window = MainWindow(
        user_manager=user_manager,
        challenge_manager=challenge_manager,
        progress_tracker=progress_tracker,
        reminder_scheduler=reminder_scheduler,
        wall_manager=wall_manager,
        theme_manager=theme_manager,
        ai_manager=db_manager,
        sync_manager=sync_manager,
    )
    print("DEBUG: MainWindow created.")
    print("DEBUG: Showing MainWindow...")
    main_window.show()
    print("DEBUG: MainWindow shown.")

    # 运行应用程序事件循环
    print("DEBUG: Starting application event loop...")
    exit_code = app.exec()
    print(f"DEBUG: Application event loop finished with exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
