from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from PySide6.QtCore import (
    QByteArray,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
    QTimer,
)

class AnimatedMessageBox(QMessageBox):
    """
    A QMessageBox subclass with fade-in and fade-out animations.
    Uses the same animation and centering logic as BaseDialog.
    """

    animation_finished = Signal()  # Signal emitted when close animation finishes

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        # --- Copied from BaseDialog --- Start
        self.setWindowOpacity(0.0)  # Start fully transparent
        # self.setModal(True) # QMessageBox handles modality differently (exec vs show)

        self._is_closing = False
        # QMessageBox uses button roles/results differently than QDialog.Accepted/Rejected
        # We'll store the clicked button role or a default if closed via 'X'
        self._result_role = QMessageBox.ButtonRole.InvalidRole

        # Fade-in animation
        self.fade_in_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Fade-out animation
        self.fade_out_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Connect fade-out finished to the handler
        self.fade_out_animation.finished.connect(self._handle_animation_finished)
        # --- Copied from BaseDialog --- End

    def showNonModal(self, auto_close_delay_ms=3000):
        """Show the message box non-modally and optionally auto-close."""
        self.setModal(False)
        # 先调整大小，这样在 showEvent 中计算居中位置时能获得正确的尺寸
        self.adjustSize()
        # 显示弹窗，这会触发 showEvent
        self.show()

        if auto_close_delay_ms > 0:
            # Use QTimer.singleShot connected to the close method
            # self.close triggers the animated closeEvent
            QTimer.singleShot(auto_close_delay_ms, self.close)

    def showEvent(self, event):
        """Override showEvent to center the dialog and trigger fade-in animation."""
        super().showEvent(event)
        # 确保窗口已经调整好大小
        if not self.isVisible():
            self.adjustSize()
        # Center the dialog on the screen
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        x = (screen.width() - dialog_geometry.width()) // 2
        y = (screen.height() - dialog_geometry.height()) // 2
        self.move(x, y)
        # Start fade-in animation
        self.fade_in_animation.start() 