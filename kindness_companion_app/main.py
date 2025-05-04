import sys
import os
import platform
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont, QFontDatabase, QScreen
from PySide6.QtCore import QFile, QTextStream, QDir, QOperatingSystemVersion, Qt, QEvent, QPoint

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
        self.theme_style = "warm"     # 默认使用温馨主题样式, 可选: "warm", "standard", "sourcio"
        self.follow_system = True     # 默认跟随系统主题

    def apply_theme(self):
        """应用当前主题，根据 theme_style 选择样式"""
        style_file_name = ""
        theme_description = ""

        # 根据当前主题和样式选择合适的样式表
        if self.theme_style == "sourcio":
            style_file_name = f"sourcio_{self.current_theme}.qss"
            theme_description = f"Sourcio {self.current_theme}"
        elif self.theme_style == "warm":
            # 保持原有的 warm 逻辑
            if self.current_theme == "dark":
                style_file_name = "warm_dark_enhanced.qss" # 或者 morandi_warm_dark.qss
                theme_description = "Warm Dark Enhanced"
            else:
                style_file_name = f"morandi_warm_{self.current_theme}.qss"
                theme_description = f"Morandi Warm {self.current_theme}"
        else: # standard
            style_file_name = f"morandi_{self.current_theme}.qss"
            theme_description = f"Morandi Standard {self.current_theme}"


        # Use the resource path prefix for loading QSS files
        style_file_path = f":/styles/{style_file_name}"
        self.logger.info(f"Attempting to load stylesheet from resource path: {style_file_path} for theme: {theme_description}")

        try:
            style_file = QFile(style_file_path)
            if style_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(style_file)
                self.app.setStyleSheet(stream.readAll())
                style_file.close()
                self.logger.info(f"已应用 {theme_description} 主题，样式表来源: {style_file_path}")
            else:
                # Log error if loading from resources fails
                self.logger.warning(f"无法从资源打开样式表文件: {style_file_path}. Error: {style_file.errorString()}")

                # Fallback to direct file path (useful during development if resources aren't updated)
                script_dir = os.path.dirname(os.path.abspath(__file__))
                fallback_style_path = os.path.join(script_dir, 'resources', 'styles', style_file_name)
                self.logger.info(f"Attempting fallback load from direct path: {fallback_style_path}")
                style_file_fallback = QFile(fallback_style_path)
                if style_file_fallback.open(QFile.ReadOnly | QFile.Text):
                     stream_fallback = QTextStream(style_file_fallback)
                     self.app.setStyleSheet(stream_fallback.readAll())
                     style_file_fallback.close()
                     self.logger.info(f"已通过后备路径应用 {theme_description} 主题: {fallback_style_path}")
                else:
                     self.logger.error(f"无法通过后备路径打开样式表文件: {fallback_style_path}. Error: {style_file_fallback.errorString()}")

        except Exception as e:
            self.logger.warning(f"加载样式表时出错: {e}")


def main():
    print("DEBUG: Starting main function...")
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
    # 临时设置 theme_style 为 "sourcio" 以便测试，后续应由设置界面控制
    # theme_manager.theme_style = "sourcio"
    print("DEBUG: Applying theme...")
    theme_manager.apply_theme() # Re-apply after changing style if needed for testing
    print("DEBUG: Theme applied.")

    # Initialize backend managers
    print("DEBUG: Initializing DatabaseManager...")
    db_manager = DatabaseManager()
    print("DEBUG: DatabaseManager initialized.")
    print("DEBUG: Initializing UserManager...")
    user_manager = UserManager(db_manager)
    print("DEBUG: UserManager initialized.")
    print("DEBUG: Initializing ChallengeManager...")
    challenge_manager = ChallengeManager(db_manager)
    print("DEBUG: ChallengeManager initialized.")
    print("DEBUG: Initializing ProgressTracker...")
    progress_tracker = ProgressTracker(db_manager)
    print("DEBUG: ProgressTracker initialized.")
    print("DEBUG: Initializing ReminderScheduler...")
    reminder_scheduler = ReminderScheduler(db_manager)
    print("DEBUG: ReminderScheduler initialized.")

    # 创建主窗口，并传入管理器实例
    print("DEBUG: Creating MainWindow...")
    main_window = MainWindow(
        user_manager=user_manager,
        challenge_manager=challenge_manager,
        progress_tracker=progress_tracker,
        reminder_scheduler=reminder_scheduler
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
