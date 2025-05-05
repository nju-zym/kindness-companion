import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QObject, QEvent, Qt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("theme_test")

class ThemeManager(QObject):
    """管理应用主题的类，支持系统主题变化的检测和自动切换"""

    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self.logger = logger
        self.current_theme = "dark"   # 默认为深色主题，根据用户偏好
        self.theme_style = "standard"  # 默认使用标准主题样式, 可选: "warm", "standard", "sourcio"
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
            self.app.setStyleSheet("""
                QWidget { background-color: #333; color: white; }
                QPushButton { background-color: #555; color: white; padding: 5px; }
                QLabel { color: white; }
            """)
        else:
            self.app.setStyleSheet("""
                QWidget { background-color: white; color: black; }
                QPushButton { background-color: #eee; color: black; padding: 5px; }
                QLabel { color: black; }
            """)

class TestWindow(QMainWindow):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("主题测试")
        self.setGeometry(100, 100, 400, 300)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)

        # 创建标签
        self.theme_label = QLabel(f"当前主题: {self.theme_manager.current_theme}")
        layout.addWidget(self.theme_label)

        # 创建按钮
        self.toggle_theme_button = QPushButton("切换主题")
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.toggle_theme_button)

        self.toggle_system_button = QPushButton("跟随系统主题" if self.theme_manager.follow_system else "手动设置主题")
        self.toggle_system_button.clicked.connect(self.toggle_system_follow)
        layout.addWidget(self.toggle_system_button)

        # 更新UI
        self.update_ui()

    def toggle_theme(self):
        if self.theme_manager.current_theme == "dark":
            self.theme_manager.current_theme = "light"
        else:
            self.theme_manager.current_theme = "dark"

        self.theme_manager.apply_theme()
        self.update_ui()

    def toggle_system_follow(self):
        self.theme_manager.follow_system = not self.theme_manager.follow_system

        if self.theme_manager.follow_system:
            # 如果启用跟随系统，立即应用系统主题
            self.theme_manager.current_theme = self.theme_manager.system_theme
            self.theme_manager.apply_theme()

        self.update_ui()

    def update_ui(self):
        self.theme_label.setText(f"当前主题: {self.theme_manager.current_theme} ({self.theme_manager.theme_style})")
        self.toggle_system_button.setText("跟随系统主题" if self.theme_manager.follow_system else "手动设置主题")

def main():
    app = QApplication(sys.argv)

    # 创建主题管理器
    theme_manager = ThemeManager(app, logger)

    # 将主题管理器存储在应用程序实例中
    app.theme_manager = theme_manager

    # 应用初始主题
    theme_manager.apply_theme()

    # 创建并显示窗口
    window = TestWindow(theme_manager)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
