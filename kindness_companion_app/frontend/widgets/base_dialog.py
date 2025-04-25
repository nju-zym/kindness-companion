from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt, QEvent
from PySide6.QtGui import QScreen

class BaseDialog(QDialog):
    """
    A base dialog class providing centering and fade animations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowOpacity(0.0) # Start fully transparent
        self.setModal(True) # Most dialogs should be modal by default

        self._is_closing = False
        self._result = QDialog.Rejected # Default result

        # Fade-in animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade-out animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Connect fade-out finished to the handler
        self.fade_out_animation.finished.connect(self._handle_animation_finished)

    def _center_window(self):
        """Centers the dialog on the parent or screen."""
        try:
            if self.parent():
                parent_rect = self.parent().geometry()
                geo = self.frameGeometry() # Use frameGeometry for size including decorations
                center_point = parent_rect.center()
                top_left = center_point - QPoint(geo.width() // 2, geo.height() // 2)
                self.move(top_left)
            else:
                # Center on the screen if no parent
                screen = QApplication.primaryScreen()
                if screen:
                    screen_geometry = screen.availableGeometry()
                    geo = self.frameGeometry()
                    center_point = screen_geometry.center()
                    top_left = center_point - QPoint(geo.width() // 2, geo.height() // 2)
                    self.move(top_left)
        except Exception as e:
            # Log error if centering fails, but don't prevent showing
            print(f"Error centering BaseDialog: {e}")

    def showEvent(self, event):
        """Override showEvent to center and trigger fade-in animation."""
        # Call super().showEvent first
        super().showEvent(event)
        # Then center the window
        self._center_window()
        self._is_closing = False # Reset closing flag on show
        # Start animation AFTER centering and super().showEvent
        self.setWindowOpacity(0.0) # Ensure starts transparent
        self.fade_in_animation.start()

    def closeEvent(self, event):
        """Override closeEvent to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            self._result = QDialog.Rejected # Default for 'X' button
            event.ignore()
            self.fade_out_animation.start()
        elif self._is_closing:
            event.ignore() # Ignore subsequent close events while animating
        else:
            event.accept() # Already faded out or never shown

    def accept(self):
        """Override accept to set result and trigger animated close."""
        if not self._is_closing:
            self._result = QDialog.Accepted
            self.close() # Triggers closeEvent

    def reject(self):
        """Override reject to set result and trigger animated close."""
        if not self._is_closing:
            self._result = QDialog.Rejected
            self.close() # Triggers closeEvent

    def done(self, result: int):
        """Override done to set result and trigger animated close."""
        if not self._is_closing:
            self._result = result
            self.close() # Triggers closeEvent

    def _handle_animation_finished(self):
        """Called after fade-out animation completes."""
        if self._is_closing:
            super().done(self._result) # Use super().done() to finish closing

