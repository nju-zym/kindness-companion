import sys
import os
import platform
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtCore import QFile, QTextStream, QDir, QOperatingSystemVersion, Qt, QEvent

from frontend.main_window import MainWindow
from backend.database_manager import DatabaseManager
from backend.user_manager import UserManager
from backend.challenge_manager import ChallengeManager
from backend.progress_tracker import ProgressTracker
from backend.reminder_scheduler import ReminderScheduler
from backend.utils import setup_logging
import resources_rc  # Import the compiled resources


def load_fonts():
    """Loads custom fonts from resources."""
    font_dir_path = ":/fonts/"  # Use the resource path prefix
    fonts_loaded = []
    font_files = [
        "Hiragino Sans GB.ttc",
        "Songti.ttc",
        "STHeiti Light.ttc",
        "STHeiti Medium.ttc"
    ]

    logging.info(f"Attempting to load fonts from resource path: {font_dir_path}")

    for font_file in font_files:
        # Construct the full resource path for each font using the alias
        resource_font_path = f"{font_dir_path}{font_file}"  # Path uses the alias directly
        logging.debug(f"Attempting to load font from resource: {resource_font_path}")

        font_id = QFontDatabase.addApplicationFont(resource_font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                # Log all families associated with the font file (TTC might have multiple)
                for family in families:
                    if family not in fonts_loaded:  # Avoid duplicates if TTC lists variations
                        fonts_loaded.append(family)
                    logging.info(f"Successfully loaded font family: {family} from {resource_font_path}")
            else:
                logging.warning(f"Loaded font from {resource_font_path} but could not retrieve family names (ID: {font_id}).")
        else:
            logging.warning(f"Failed to load font from resource: {resource_font_path}. Check path and QRC compilation.")
            # Keep the development path check as a fallback if needed, but prioritize resources
            dev_font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources', 'fonts', font_file))
            if os.path.exists(dev_font_path):
                logging.info(f"Attempting fallback load from dev path: {dev_font_path}")
                font_id_dev = QFontDatabase.addApplicationFont(dev_font_path)
                if font_id_dev != -1:
                    families_dev = QFontDatabase.applicationFontFamilies(font_id_dev)
                    if families_dev:
                        for family_dev in families_dev:
                            if family_dev not in fonts_loaded:
                                fonts_loaded.append(family_dev)
                            logging.info(f"Successfully loaded font family (dev path): {family_dev} from {dev_font_path}")
                    else:
                        logging.warning(f"Loaded font from dev path {dev_font_path} but could not retrieve family names (ID: {font_id_dev}).")
                else:
                    logging.warning(f"Failed to load font (dev path): {dev_font_path}")

    if not fonts_loaded:
        logging.error("No custom fonts were loaded successfully!")
    else:
        # Log all available families after attempting to load all fonts
        logging.info(f"Available application font families after loading: {QFontDatabase.families()}")

    return list(set(fonts_loaded))  # Return unique list


class ThemeManager:
    """管理应用主题的类，支持系统主题变化的检测和自动切换"""

    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.current_theme = "light"  # 默认为浅色主题

        # 检测当前系统主题
        self.detect_system_theme()

        # 应用当前主题
        self.apply_theme()

        # 监听系统主题变化（在支持的平台上）
        if self.is_theme_detection_supported():
            # ThemeManager 必须继承 QObject 才能作为事件过滤器
            # 所以这里不直接安装事件过滤器，而是在 main() 中处理
            self.logger.info("已准备系统主题变化监听")

    def detect_system_theme(self):
        """检测系统当前的主题设置"""
        try:
            if platform.system() == "Darwin":  # macOS
                # 使用 try-except 包裹 Foundation 导入，避免缺少模块时崩溃
                try:
                    # 尝试使用 PyObjC
                    from AppKit import NSApp
                    from Foundation import NSUserDefaults
                    # 检查是否启用了深色模式
                    dark_mode = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
                    self.current_theme = "dark" if dark_mode == "Dark" else "light"
                    self.logger.info(f"检测到macOS系统主题: {self.current_theme}")
                except ImportError:
                    # 如果无法导入 Foundation，则使用默认主题
                    self.logger.warning("无法导入 Foundation 模块，需要安装 PyObjC 以支持自动检测系统主题")
                    self.logger.warning("可执行 'pip install pyobjc' 安装所需库")
                    self.current_theme = "light"  # 默认使用浅色主题
            elif platform.system() == "Windows":  # Windows
                # Windows 10及以上版本支持深色模式
                if QOperatingSystemVersion.current() >= QOperatingSystemVersion.Windows10:
                    import winreg
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                         r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                            # 0表示深色模式，1表示浅色模式
                            value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                            self.current_theme = "light" if value == 1 else "dark"
                            self.logger.info(f"检测到Windows系统主题: {self.current_theme}")
                    except Exception as e:
                        self.logger.warning(f"无法检测Windows系统主题：{e}，使用默认浅色主题")
                        self.current_theme = "light"
            elif platform.system() == "Linux":  # Linux（需要根据桌面环境调整）
                # 尝试检测GNOME桌面环境下的主题
                try:
                    import subprocess
                    result = subprocess.run(
                        ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                        capture_output=True, text=True
                    )
                    # 简单判断主题名称是否包含"dark"或"Dark"关键字
                    theme_name = result.stdout.strip().lower()
                    self.current_theme = "dark" if "dark" in theme_name else "light"
                    self.logger.info(f"检测到Linux GNOME系统主题: {self.current_theme}")
                except Exception as e:
                    self.logger.warning(f"无法检测Linux系统主题：{e}，使用默认浅色主题")
                    self.current_theme = "light"
        except Exception as e:
            self.logger.warning(f"主题检测过程中发生错误：{e}，使用默认浅色主题")
            self.current_theme = "light"

    def is_theme_detection_supported(self):
        """检查当前平台是否支持主题变化检测"""
        system = platform.system()
        if system == "Darwin":  # macOS
            try:
                # 检查是否可以导入 Foundation
                import Foundation
                return True
            except ImportError:
                self.logger.warning("macOS主题检测需要PyObjC库")
                return False
        elif system == "Windows":  # Windows 10+
            return QOperatingSystemVersion.current() >= QOperatingSystemVersion.Windows10
        elif system == "Linux":  # Linux（目前不支持自动检测变化）
            return False
        return False

    def apply_theme(self):
        """应用当前主题"""
        style_file_name = "main.qss" if self.current_theme == "light" else "dark.qss"
        # Use absolute path based on the script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        style_file_path = os.path.join(script_dir, 'resources', 'styles', style_file_name)
        self.logger.info(f"Attempting to load stylesheet from: {style_file_path}") # Log the absolute path

        try:
            style_file = QFile(style_file_path)
            if style_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(style_file)
                self.app.setStyleSheet(stream.readAll())
                style_file.close()
                self.logger.info(f"已应用{self.current_theme}主题，样式表来源: {style_file_path}")
            else:
                self.logger.warning(f"无法打开样式表文件: {style_file_path}. Error: {style_file.errorString()}") # Log error string
        except Exception as e:
            self.logger.warning(f"加载样式表时出错: {e}")

    def on_palette_change(self):
        """当系统调色板变化时调用此方法"""
        self.logger.info("检测到系统主题变化，正在更新应用主题...")
        self.detect_system_theme()
        self.apply_theme()


def main():
    """Main application entry point."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Kindness Challenge application")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("善行挑战")

    # Load custom fonts *before* loading stylesheet or creating widgets
    loaded_font_families = load_fonts()
    logger.info(f"Loaded font families reported by load_fonts: {loaded_font_families}")

    # Set default application font
    default_font_family = "Hiragino Sans GB"  # Or choose another preferred font
    if default_font_family not in loaded_font_families:
        logger.warning(f"Preferred default font '{default_font_family}' not loaded. Trying fallback.")
        fallback_options = ["STHeiti Light", "Songti SC"] + loaded_font_families
        found_fallback = False
        for option in fallback_options:
            if option in loaded_font_families:
                default_font_family = option
                found_fallback = True
                break
        if not found_fallback:
            logger.error("No suitable fallback font found in loaded list.")
            default_font_family = None  # Rely on system default if no custom fonts work

    if default_font_family:
        default_font_size = 16  # Increased from 14 to 16
        app_font = QFont(default_font_family, default_font_size)
        app.setFont(app_font)
        logger.info(f"Set application default font to: {default_font_family}, Size: {default_font_size}pt")
    else:
        logger.warning("Could not set a custom default font. Using system default.")

    # Set application icon
    icon_path = ":/icons/app_icon.png"  # 使用资源路径而不是文件系统路径
    app_icon = QIcon(icon_path)
    if app_icon.isNull():
        logger.warning(f"Could not load application icon from {icon_path}. Using default icon.")
    else:
        app.setWindowIcon(app_icon)
        logger.info(f"Loaded application icon from {icon_path}")

    # 创建主题管理器并初始化
    theme_manager = ThemeManager(app, logger)

    # 为应用程序设置事件处理，实现对系统主题变化的监控
    # 使用函数而非直接通过 installEventFilter 实现
    if platform.system() == "Darwin":  # macOS
        # 监听 ApplicationPaletteChange 事件
        app.paletteChanged.connect(theme_manager.on_palette_change)
        logger.info("已启用macOS系统主题变化监听")
    elif platform.system() == "Windows" and QOperatingSystemVersion.current() >= QOperatingSystemVersion.Windows10:
        # Windows 10+ 监听应用样式变化
        app.styleChanged.connect(lambda: theme_manager.on_palette_change())
        logger.info("已启用Windows系统主题变化监听")

    # Initialize backend components
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    challenge_manager = ChallengeManager(db_manager)
    progress_tracker = ProgressTracker(db_manager)
    # Create the reminder scheduler instance
    reminder_scheduler = ReminderScheduler(db_manager) # Store the instance

    # Add default user if it doesn't exist
    default_user = user_manager.login("zym", "1")
    if not default_user:
        logger.info("Creating default user 'zym'")
        user_manager.register_user("zym", "1")

    # Create and show main window
    main_window = MainWindow(
        user_manager,
        challenge_manager,
        progress_tracker,
        reminder_scheduler # Pass the instance
    )

    # Connect the scheduler shutdown to the application's aboutToQuit signal
    app.aboutToQuit.connect(reminder_scheduler.shutdown)
    logger.info("Connected reminder_scheduler.shutdown to app.aboutToQuit")

    # Connect the database disconnect to the application's aboutToQuit signal
    app.aboutToQuit.connect(db_manager.disconnect)
    logger.info("Connected db_manager.disconnect to app.aboutToQuit")

    main_window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
