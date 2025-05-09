from PySide6.QtWidgets import QMessageBox, QWidget, QDialog, QApplication

# Make sure QPoint is imported
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    Signal,
    Slot,
    QPoint,
    QEvent,
    QByteArray,
    QRect,
    QSize,
)
from PySide6.QtGui import QScreen


# Keep inheriting from QMessageBox
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

    # --- Copied from BaseDialog (_center_window logic) --- Start
    def _center_window(self):
        """Centers the dialog on the parent's window or screen."""
        try:
            parent_widget = self.parent()
            if parent_widget:
                # --- Use parent's top-level window for centering --- Start
                parent_rect = QRect(
                    0, 0, 400, 300
                )  # Default size if we can't get actual size
                if isinstance(parent_widget, QWidget):
                    parent_rect.setWidth(parent_widget.width())
                    parent_rect.setHeight(parent_widget.height())
                    parent_rect.moveTopLeft(
                        QPoint(parent_widget.x(), parent_widget.y())
                    )
                # --- Use parent's top-level window for centering --- End
                geo = (
                    self.frameGeometry()
                )  # Use frameGeometry for size including decorations
                center_point = parent_rect.center()
                top_left = center_point - QPoint(geo.width() // 2, geo.height() // 2)
                # Ensure the dialog doesn't go off-screen (optional but good practice)
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                top_left.setX(
                    max(
                        screen_geometry.left(),
                        min(top_left.x(), screen_geometry.right() - geo.width()),
                    )
                )
                top_left.setY(
                    max(
                        screen_geometry.top(),
                        min(top_left.y(), screen_geometry.bottom() - geo.height()),
                    )
                )
                self.move(top_left)
            else:
                # Center on the screen if no parent
                screen = QApplication.primaryScreen()
                if screen:
                    screen_geometry = screen.availableGeometry()
                    geo = self.frameGeometry()
                    center_point = screen_geometry.center()
                    top_left = center_point - QPoint(
                        geo.width() // 2, geo.height() // 2
                    )
                    self.move(top_left)
        except Exception as e:
            # Log error if centering fails, but don't prevent showing
            print(f"Error centering AnimatedMessageBox: {e}")

    # --- Copied from BaseDialog (_center_window logic) --- End

    # --- Copied/Adapted from BaseDialog --- Start
    def showEvent(self, event):
        """Override showEvent to center and trigger fade-in animation."""
        # Call super().showEvent first
        super().showEvent(event)
        # Then center the window
        self._center_window()
        self._is_closing = False  # Reset closing flag on show
        # Start animation AFTER centering and super().showEvent
        self.setWindowOpacity(0.0)  # Ensure starts transparent
        self.fade_in_animation.start()

    def closeEvent(self, event):
        """Override closeEvent to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            # For QMessageBox, closing via 'X' usually means RejectRole or NoRole depending on buttons
            # Let's default to RejectRole, exec() will handle the actual return value.
            self._result_role = QMessageBox.ButtonRole.RejectRole
            event.ignore()
            self.fade_out_animation.start()
        elif self._is_closing:
            event.ignore()  # Ignore subsequent close events while animating
        else:
            # If already transparent or not shown, accept the event to allow normal closing
            # This case might happen if close() is called before show() or after fade-out
            event.accept()

    # QMessageBox doesn't have accept/reject like QDialog.
    # Instead, clicking buttons calls done() with the button's role.
    # We override done() to handle the animation.

    def done(self, role: int):  # role is typically QMessageBox.ButtonRole
        """Override done to set result role and trigger animated close."""
        # Only start closing animation if not already closing and visible
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            self._result_role = role  # Store the role of the button clicked
            # Don't call super().done() yet, start animation
            self.fade_out_animation.start()
        elif not self._is_closing:
            # If done() is called when not visible (e.g., programmatically before show()),
            # just call the original done() to set the result immediately.
            super().done(role)

    def _handle_animation_finished(self):
        """Called after fade-out animation completes."""
        if self._is_closing:
            # Map the stored button role/enum to the integer result code
            result_code = QDialog.DialogCode.Rejected  # Default to Rejected

            # Check if it's a StandardButton enum
            if isinstance(self._result_role, QMessageBox.StandardButton):
                # Map standard buttons that typically mean acceptance
                if self._result_role in [
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Yes,
                    QMessageBox.StandardButton.Save,
                    QMessageBox.StandardButton.Open,
                    QMessageBox.StandardButton.Apply,  # Added Apply as acceptance
                ]:
                    result_code = QDialog.DialogCode.Accepted
                # Other standard buttons (Cancel, No, Abort, etc.) default to Rejected

            # Check if it's a ButtonRole enum (less common for standard buttons but possible)
            elif isinstance(self._result_role, QMessageBox.ButtonRole):
                # Map button roles that typically mean acceptance
                if self._result_role in [
                    QMessageBox.ButtonRole.AcceptRole,
                    QMessageBox.ButtonRole.YesRole,
                    QMessageBox.ButtonRole.ApplyRole,
                ]:
                    result_code = QDialog.DialogCode.Accepted
                # Other roles (RejectRole, NoRole, DestructiveRole, etc.) default to Rejected

            # Now call the original QDialog.done() with the correct integer result code
            QDialog.done(self, result_code)
            self.animation_finished.emit()  # Emit signal after closing
            # Resetting flag is handled in showEvent

    # --- Copied/Adapted from BaseDialog --- End

    def showNonModal(self, auto_close_delay_ms=3000):
        """Show the message box non-modally and optionally auto-close."""
        self.setModal(False)
        self.show()  # Triggers showEvent for centering and fade-in

        if auto_close_delay_ms > 0:
            # Use QTimer.singleShot connected to the close method
            # self.close triggers the animated closeEvent
            QTimer.singleShot(auto_close_delay_ms, self.close)

    # --- Static Methods (remain largely the same) ---
    # They now benefit from the updated animation/centering logic when creating instances
    @staticmethod
    def showInformation(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
    ) -> int:
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec()

    @staticmethod
    def showWarning(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
    ) -> int:
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec()

    @staticmethod
    def showCritical(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
    ) -> int:
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec()

    @staticmethod
    def showQuestion(
        parent: QWidget | None,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No,
        defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
    ) -> int:
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec()

    @staticmethod
    def show_info():
        """Example of using showInformation."""
        reply = AnimatedMessageBox.showInformation(
            None,
            "信息",
            "这是一个信息提示。",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.NoButton,
        )
        print(f"Info Reply: {reply}")  # Prints the result after closing

    @staticmethod
    def show_warn():
        """Example of using showWarning."""
        reply = AnimatedMessageBox.showWarning(
            None,
            "警告",
            "这是一个警告提示。",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.NoButton,
        )
        print(f"Warning Reply: {reply}")  # Prints the result after closing

    @staticmethod
    def show_quest():
        """Example of using showQuestion."""
        reply = AnimatedMessageBox.showQuestion(
            None,
            "问题",
            "这是一个问题，请选择 Yes 或 No?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.NoButton,
        )
        print(f"Question Reply: {reply}")  # Prints the result after closing

    @staticmethod
    def show_non_modal():
        """Example of using showNonModal."""
        msgBox = AnimatedMessageBox(None)
        msgBox.setWindowTitle("非模态")
        msgBox.setText("这是一个非模态消息框，3秒后自动关闭。")
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.showNonModal(3000)  # Auto-close after 3 seconds

    @staticmethod
    def show_custom_dialog():
        """Example of using the class directly for more complex dialogs."""
        dialog = AnimatedMessageBox(None)
        dialog.setWindowTitle("自定义对话框")
        dialog.setText("这是一个可以添加自定义按钮的对话框。")
        dialog.setIcon(QMessageBox.Icon.Information)
        custom_button = dialog.addButton(
            "自定义操作", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() == custom_button:
            print("自定义操作按钮被点击")
        else:
            print("取消按钮被点击")


# Example Usage (if run directly)
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout

    app = QApplication(sys.argv)

    main_widget = QWidget()
    layout = QVBoxLayout(main_widget)

    def show_info():
        AnimatedMessageBox.showInformation(main_widget, "信息", "这是一条信息提示。")

    def show_warn():
        AnimatedMessageBox.showWarning(main_widget, "警告", "这是一条警告信息。")

    def show_quest():
        reply = AnimatedMessageBox.showQuestion(
            main_widget,
            "问题",
            "这是一个问题，请选择 Yes 或 No?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        print(f"Question Reply: {reply}")  # Prints the result after closing

    def show_non_modal():
        non_modal_msg = AnimatedMessageBox(main_widget)
        non_modal_msg.setWindowTitle("非模态提示")
        non_modal_msg.setText("这条消息将在3秒后自动关闭。")
        non_modal_msg.setIcon(QMessageBox.Icon.Information)
        non_modal_msg.showNonModal(3000)

    def show_custom_dialog():
        # Example of using the class directly for more complex dialogs
        dialog = AnimatedMessageBox(main_widget)
        dialog.setWindowTitle("自定义对话框")
        dialog.setText("这是一个可以添加自定义按钮的对话框。")
        dialog.setIcon(QMessageBox.Icon.Information)
        custom_button = dialog.addButton(
            "自定义操作", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() == custom_button:
            print("自定义操作按钮被点击")
        else:
            print("取消按钮被点击")

    btn_info = QPushButton("显示信息")
    btn_info.clicked.connect(show_info)
    layout.addWidget(btn_info)

    btn_warn = QPushButton("显示警告")
    btn_warn.clicked.connect(show_warn)
    layout.addWidget(btn_warn)

    btn_quest = QPushButton("显示问题")
    btn_quest.clicked.connect(show_quest)
    layout.addWidget(btn_quest)

    btn_non_modal = QPushButton("显示非模态 (自动关闭)")
    btn_non_modal.clicked.connect(show_non_modal)
    layout.addWidget(btn_non_modal)

    btn_custom = QPushButton("显示自定义对话框")
    btn_custom.clicked.connect(show_custom_dialog)
    layout.addWidget(btn_custom)

    main_widget.show()
    sys.exit(app.exec())
