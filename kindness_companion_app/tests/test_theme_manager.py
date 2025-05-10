import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.theme_manager import ThemeManager


class TestThemeManager(unittest.TestCase):
    """Test cases for the theme manager."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        # Create QApplication instance
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        """Set up test fixtures for each test method."""
        # Create a mock logger
        self.mock_logger = MagicMock()

        # Create the theme manager instance
        self.theme_manager = ThemeManager(self.app, self.mock_logger)

    def test_initialization(self):
        """Test theme manager initialization."""
        # Verify that the theme manager was initialized correctly
        self.assertIsNotNone(self.theme_manager)
        self.assertIsNotNone(self.theme_manager.logger)
        self.assertIsNotNone(self.theme_manager.theme_style)
        self.assertIsNotNone(self.theme_manager.theme_colors)
        self.assertIsNotNone(self.theme_manager.theme_styles)

    def test_theme_colors(self):
        """Test theme colors."""
        # Verify that all required colors are present
        required_colors = ["primary", "secondary", "background", "text"]
        for color in required_colors:
            value = self.theme_manager.get_color(color)
            self.assertIsInstance(value, str)
            self.assertTrue(value.startswith("#"))

    def test_theme_styles(self):
        """Test theme styles."""
        # Verify that all required styles are present
        required_styles = ["button", "label", "input", "container"]
        for style in required_styles:
            self.assertIn(style, self.theme_manager.theme_styles)
            self.assertIsNotNone(self.theme_manager.get_style(style))

    def test_theme_switching(self):
        """Test theme switching."""
        # Test switching to dark theme
        self.theme_manager.theme_style = "dark"
        self.theme_manager.apply_theme()
        self.assertEqual(self.theme_manager.theme_style, "dark")

        # Test switching to light theme
        self.theme_manager.theme_style = "light"
        self.theme_manager.apply_theme()
        self.assertEqual(self.theme_manager.theme_style, "light")

        # Test switching to standard theme
        self.theme_manager.theme_style = "standard"
        self.theme_manager.apply_theme()
        self.assertEqual(self.theme_manager.theme_style, "standard")

    def test_invalid_theme(self):
        """Test handling of invalid theme."""
        # Try to set an invalid theme
        self.theme_manager.theme_style = "invalid_theme"
        self.theme_manager.apply_theme()

        # Verify that it falls back to standard theme
        self.assertEqual(self.theme_manager.theme_style, "standard")

    def test_theme_consistency(self):
        """Test theme consistency."""
        # Get all theme styles
        theme_styles = ["standard", "dark", "light"]

        for style in theme_styles:
            self.theme_manager.theme_style = style
            self.theme_manager.apply_theme()

            # Verify that all required colors are present
            required_colors = ["primary", "secondary", "background", "text"]
            for color in required_colors:
                value = self.theme_manager.get_color(color)
                self.assertIsInstance(value, str)
                self.assertTrue(value.startswith("#"))

            # Verify that all required styles are present
            required_styles = ["button", "label", "input", "container"]
            for style_name in required_styles:
                style_str = self.theme_manager.get_style(style_name)
                self.assertIsInstance(style_str, str)
                self.assertTrue(len(style_str) > 0)

    def test_theme_application(self):
        """Test theme application."""
        # Create a mock for setStyleSheet
        with patch.object(self.app, "setStyleSheet") as mock_set_style_sheet:
            # Apply the theme
            self.theme_manager.apply_theme()

            # Verify that setStyleSheet was called
            mock_set_style_sheet.assert_called_once()

            # Get the stylesheet that was applied
            stylesheet = mock_set_style_sheet.call_args[0][0]
            self.assertIsNotNone(stylesheet)
            self.assertTrue(len(stylesheet) > 0)

            # Verify that the stylesheet contains expected components
            self.assertIn("QPushButton", stylesheet)
            self.assertIn("QLabel", stylesheet)
            self.assertIn("QLineEdit", stylesheet)
            self.assertIn("QWidget", stylesheet)


if __name__ == "__main__":
    unittest.main()
