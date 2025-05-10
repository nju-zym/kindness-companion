import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


class ThemeManager:
    """Manages application themes and styles."""

    def __init__(self, app, logger=None):
        """
        Initialize the theme manager.

        Args:
            app: QApplication instance
            logger: Logger instance (optional)
        """
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self.theme_style = "standard"

        # Define theme colors
        self.theme_colors = {
            "standard": {
                "primary": "#4A90E2",
                "primary_dark": "#357ABD",
                "primary_light": "#6BA4E7",
                "background": "#FFFFFF",
                "text": "#333333",
                "secondary": "#F5F5F5",
                "accent": "#FF6B6B",
            },
            "dark": {
                "primary": "#5C6BC0",
                "primary_dark": "#3949AB",
                "primary_light": "#7986CB",
                "background": "#1E1E1E",
                "text": "#FFFFFF",
                "secondary": "#2D2D2D",
                "accent": "#FF5252",
            },
            "light": {
                "primary": "#2196F3",
                "primary_dark": "#1976D2",
                "primary_light": "#64B5F6",
                "background": "#F5F5F5",
                "text": "#212121",
                "secondary": "#FFFFFF",
                "accent": "#FF4081",
            },
        }

        # Define theme styles
        self.theme_styles = {
            "button": "QPushButton{background-color:{primary};color:white;border:none;padding:8px 16px;border-radius:4px;}QPushButton:hover{background-color:{primary_dark};}QPushButton:pressed{background-color:{primary_light};}",
            "label": "QLabel{color:{text};font-size:14px;}",
            "input": "QLineEdit,QTextEdit{background-color:{background};color:{text};border:1px solid {primary};border-radius:4px;padding:8px;}QLineEdit:focus,QTextEdit:focus{border:2px solid {primary};}",
            "container": "QWidget{background-color:{background};color:{text};}",
        }

        # Apply initial theme
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to the application."""
        try:
            # Get current theme colors
            colors = self.theme_colors[self.theme_style]

            # Generate stylesheet
            stylesheet = ""
            for style_name, style_template in self.theme_styles.items():
                stylesheet += style_template.format(**colors)

            # Apply stylesheet
            self.app.setStyleSheet(stylesheet)
            self.logger.info(f"Applied {self.theme_style} theme")

        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
            # Revert to standard theme if there's an error
            self.theme_style = "standard"
            self.apply_theme()

    def get_color(self, color_name):
        """
        Get a color from the current theme.

        Args:
            color_name: Name of the color to get

        Returns:
            str: Color value in hex format
        """
        return self.theme_colors[self.theme_style].get(color_name, "#000000")

    def get_style(self, style_name):
        """
        Get a style from the current theme.

        Args:
            style_name: Name of the style to get

        Returns:
            str: Style definition
        """
        style_template = self.theme_styles.get(style_name, "")
        if not style_template:
            return ""

        colors = self.theme_colors[self.theme_style]
        return style_template.format(**colors)

    @property
    def current_colors(self):
        """获取当前主题的颜色字典"""
        return self.theme_colors[self.theme_style]
