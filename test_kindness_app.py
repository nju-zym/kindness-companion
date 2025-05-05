import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QRadioButton, QButtonGroup, QGroupBox, QHBoxLayout
from PySide6.QtCore import QObject, QEvent, Qt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kindness_app_test")

class ThemeManager(QObject):
    """管理应用主题的类，支持系统主题变化的检测和自动切换"""

    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self.logger = logger
        self.current_theme = "dark"   # 默认为深色主题，根据用户偏好
        self.theme_style = "sourcio"  # 默认使用Sourcio主题样式, 可选: "warm", "standard", "sourcio"
        self.follow_system = False    # 默认不跟随系统主题，固定使用深色主题

        # 创建系统主题变化监听器
        self.app.installEventFilter(self)

        # 初始检测系统主题
        self.system_theme = self.detect_system_theme()
        self.logger.info(f"初始系统主题检测: {self.system_theme}")

    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获系统主题变化事件"""
        if event.type() == QEvent.ApplicationPaletteChange:
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
        # 使用 Qt 的调色板检测系统主题
        app_palette = self.app.palette()
        # 获取窗口背景色
        window_color = app_palette.color(app_palette.ColorRole.Window)
        # 计算亮度 (0-255)，使用标准RGB亮度公式
        brightness = (0.299 * window_color.red() +
                     0.587 * window_color.green() +
                     0.114 * window_color.blue())

        # 如果亮度大于127.5（中间值），则认为是浅色主题
        if brightness > 127.5:
            self.logger.info(f"检测到系统使用浅色主题 (亮度: {brightness})")
            return "light"
        else:
            self.logger.info(f"检测到系统使用深色主题 (亮度: {brightness})")
            return "dark"

    def apply_theme(self):
        """应用当前主题，根据 theme_style 选择样式"""
        # 如果设置为跟随系统主题，则使用系统主题
        if self.follow_system:
            self.current_theme = self.system_theme
            self.logger.info(f"跟随系统主题: {self.current_theme}")

        # 在这里应用主题样式表
        self.logger.info(f"应用主题: {self.current_theme}, 样式: {self.theme_style}")

        # 简单的样式表示例
        if self.current_theme == "dark":
            if self.theme_style == "sourcio":
                self.app.setStyleSheet("""
                    QWidget { background-color: #2A2F3A; color: #E8E9EC; }
                    QPushButton { background-color: #3A4050; color: white; padding: 8px; border-radius: 4px; }
                    QLabel { color: #E8E9EC; }
                    QGroupBox { border: 1px solid #3A4050; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: #E8E9EC; }
                """)
            elif self.theme_style == "warm":
                self.app.setStyleSheet("""
                    QWidget { background-color: #2D2A3E; color: #F0EAF4; }
                    QPushButton { background-color: #413A5A; color: white; padding: 8px; border-radius: 4px; }
                    QLabel { color: #F0EAF4; }
                    QGroupBox { border: 1px solid #413A5A; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: #F0EAF4; }
                """)
            else:  # standard
                self.app.setStyleSheet("""
                    QWidget { background-color: #333; color: white; }
                    QPushButton { background-color: #555; color: white; padding: 8px; border-radius: 4px; }
                    QLabel { color: white; }
                    QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: white; }
                """)
        else:  # light
            if self.theme_style == "sourcio":
                self.app.setStyleSheet("""
                    QWidget { background-color: #F7F5F2; color: #6D6875; }
                    QPushButton { background-color: #E67E22; color: white; padding: 8px; border-radius: 4px; }
                    QLabel { color: #6D6875; }
                    QGroupBox { border: 1px solid #E0DDD5; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: #6D6875; }
                """)
            elif self.theme_style == "warm":
                self.app.setStyleSheet("""
                    QWidget { background-color: #FFF8F0; color: #5D4E60; }
                    QPushButton { background-color: #E67E22; color: white; padding: 8px; border-radius: 4px; }
                    QLabel { color: #5D4E60; }
                    QGroupBox { border: 1px solid #F0E6D8; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: #5D4E60; }
                """)
            else:  # standard
                self.app.setStyleSheet("""
                    QWidget { background-color: white; color: black; }
                    QPushButton { background-color: #eee; color: black; padding: 8px; border-radius: 4px; }
                    QLabel { color: black; }
                    QGroupBox { border: 1px solid #ddd; border-radius: 4px; margin-top: 1em; padding-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
                    QRadioButton { color: black; }
                """)

class ThemeSettingsWidget(QWidget):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 主题信息标签
        self.info_label = QLabel(f"当前主题: {self.theme_manager.current_theme}, 样式: {self.theme_manager.theme_style}")
        layout.addWidget(self.info_label)

        # 主题模式设置
        self.theme_mode_group = QGroupBox("主题模式")
        theme_mode_layout = QHBoxLayout(self.theme_mode_group)

        self.system_radio = QRadioButton("跟随系统")
        self.light_radio = QRadioButton("浅色模式")
        self.dark_radio = QRadioButton("深色模式")

        # 根据当前设置选中相应的单选按钮
        if self.theme_manager.follow_system:
            self.system_radio.setChecked(True)
        elif self.theme_manager.current_theme == "light":
            self.light_radio.setChecked(True)
        else:
            self.dark_radio.setChecked(True)

        theme_mode_layout.addWidget(self.system_radio)
        theme_mode_layout.addWidget(self.light_radio)
        theme_mode_layout.addWidget(self.dark_radio)

        layout.addWidget(self.theme_mode_group)

        # 主题样式设置
        self.theme_style_group = QGroupBox("主题风格")
        theme_style_layout = QHBoxLayout(self.theme_style_group)

        self.standard_radio = QRadioButton("标准风格")
        self.warm_radio = QRadioButton("温馨风格")
        self.sourcio_radio = QRadioButton("Sourcio风格")

        # 根据当前设置选中相应的单选按钮
        if self.theme_manager.theme_style == "standard":
            self.standard_radio.setChecked(True)
        elif self.theme_manager.theme_style == "warm":
            self.warm_radio.setChecked(True)
        else:
            self.sourcio_radio.setChecked(True)

        theme_style_layout.addWidget(self.standard_radio)
        theme_style_layout.addWidget(self.warm_radio)
        theme_style_layout.addWidget(self.sourcio_radio)

        layout.addWidget(self.theme_style_group)

        # 应用按钮
        self.apply_button = QPushButton("应用主题设置")
        self.apply_button.clicked.connect(self.apply_theme_settings)
        layout.addWidget(self.apply_button)

    def apply_theme_settings(self):
        # 获取主题模式设置
        if self.system_radio.isChecked():
            self.theme_manager.follow_system = True
            current_system_theme = self.theme_manager.detect_system_theme()
            self.theme_manager.current_theme = current_system_theme
        else:
            self.theme_manager.follow_system = False
            if self.light_radio.isChecked():
                self.theme_manager.current_theme = "light"
            else:
                self.theme_manager.current_theme = "dark"

        # 获取主题样式设置
        if self.standard_radio.isChecked():
            self.theme_manager.theme_style = "standard"
        elif self.warm_radio.isChecked():
            self.theme_manager.theme_style = "warm"
        else:
            self.theme_manager.theme_style = "sourcio"

        # 应用主题
        self.theme_manager.apply_theme()

        # 更新信息标签
        self.info_label.setText(f"当前主题: {self.theme_manager.current_theme}, 样式: {self.theme_manager.theme_style}")

class MainWindow(QMainWindow):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("善行伴侣 - 主题设置测试")
        self.setGeometry(100, 100, 600, 400)

        # 创建主题设置部件
        self.theme_settings = ThemeSettingsWidget(self.theme_manager)
        self.setCentralWidget(self.theme_settings)

def main():
    app = QApplication(sys.argv)

    # 创建主题管理器
    theme_manager = ThemeManager(app, logger)

    # 将主题管理器存储在应用程序实例中
    app.theme_manager = theme_manager

    # 应用初始主题
    theme_manager.apply_theme()

    # 创建并显示窗口
    window = MainWindow(theme_manager)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
