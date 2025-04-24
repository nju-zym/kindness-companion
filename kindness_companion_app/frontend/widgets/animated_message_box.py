from PySide6.QtWidgets import QMessageBox, QWidget, QDialog, QApplication
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Signal, Slot
from PySide6.QtGui import QScreen


class AnimatedMessageBox(QMessageBox):
    """
    A QMessageBox subclass with fade-in and fade-out animations.
    Provides static methods similar to QMessageBox and a non-modal option.
    """
    animation_finished = Signal() # Signal emitted when close animation finishes

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowOpacity(0.0) # Start fully transparent

        # Fade-in animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300) # Adjust duration as needed
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade-out animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300) # Adjust duration as needed
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Connect fade-out finished to actually close the dialog
        self.fade_out_animation.finished.connect(self._handle_animation_finished)

        self._is_closing = False # Flag to prevent multiple close attempts
        self._result = QMessageBox.NoButton # Store result for accept/reject

    def _handle_animation_finished(self):
        """Called after fade-out animation completes."""
        self._is_closing = False # Reset flag
        # Use done() which handles both accept and reject based on _result (now an int)
        super().done(self._result) # Pass the integer result
        self.animation_finished.emit() # Emit signal after closing

    def showEvent(self, event):
        """Override showEvent to trigger fade-in animation."""
        # Center the window before showing
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.center() - self.rect().center())
        else:
            # Center on the screen if no parent
            screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
            self.move(screen_geometry.center() - self.rect().center())

        self.fade_in_animation.start()
        super().showEvent(event)

    def closeEvent(self, event):
        """Override closeEvent to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            event.ignore() # Ignore the immediate close request
            # Default result for closing via 'X' is Rejected
            self._result = QDialog.Rejected # Use integer result code
            self.fade_out_animation.start()
        else:
            # Allow close if already closing or transparent
            # Check if the event is spontaneous (system-generated) before accepting
            if not event.spontaneous() or self._is_closing:
                 super().closeEvent(event)
            else:
                 # If spontaneous and not already closing, ignore it
                 # as the animation should handle the closing.
                 event.ignore()


    def accept(self):
        """Override accept to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            self._result = QDialog.Accepted # Use integer result code
            self.fade_out_animation.start()
        # Do not call super().accept() here, wait for animation

    def reject(self):
        """Override reject to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            self._result = QDialog.Rejected # Use integer result code
            self.fade_out_animation.start()
        # Do not call super().reject() here, wait for animation

    def done(self, result: int): # Ensure result is an integer
        """Override done to trigger fade-out animation."""
        if not self._is_closing and self.windowOpacity() > 0:
            self._is_closing = True
            self._result = result # Store the integer result
            self.fade_out_animation.start()
        # Do not call super().done() here, wait for animation

    def showNonModal(self, auto_close_delay_ms=3000):
        """Show the message box non-modally and optionally auto-close."""
        self.setModal(False)
        self.show() # Triggers showEvent for fade-in

        if auto_close_delay_ms > 0:
            # Use QTimer.singleShot connected to the close method
            # Use self.close which triggers the fade-out animation
            QTimer.singleShot(auto_close_delay_ms, self.close)

    # --- Static Methods ---
    # Ensure static methods return the integer result from exec()
    @staticmethod
    def showInformation(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec() # exec() returns the integer result

    @staticmethod
    def showWarning(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec() # exec() returns the integer result

    @staticmethod
    def showCritical(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        return msgBox.exec() # exec() returns the integer result

    @staticmethod
    def showQuestion(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.NoButton):
        msgBox = AnimatedMessageBox(parent)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setStandardButtons(buttons)
        msgBox.setDefaultButton(defaultButton)
        # Map the result of exec() back to QMessageBox standard buttons if needed by caller
        # For now, just return the integer result (e.g., QDialog.Accepted for Yes, QDialog.Rejected for No)
        result_int = msgBox.exec()
        # The caller compares with QMessageBox.Yes/No etc. QMessageBox maps these internally.
        # Let's return the standard button enum value corresponding to the int result
        button_clicked = msgBox.button(result_int) # Get the button corresponding to the result code
        if button_clicked:
            role = msgBox.buttonRole(button_clicked)
            standard_button = msgBox.standardButton(button_clicked)
            if standard_button != QMessageBox.NoButton:
                 return standard_button # Return QMessageBox.Yes, QMessageBox.No etc.
            # Handle custom buttons if necessary based on role, otherwise fallback
        # Fallback or if no button matched (e.g., closed via 'X')
        return QMessageBox.No # Or another appropriate default

# Example Usage (if run directly)
if __name__ == '__main__':
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
        reply = AnimatedMessageBox.showQuestion(main_widget, "问题", "这是一个问题，请选择 Yes 或 No?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        print(f"Question Reply: {reply}") # Prints the result after closing

    def show_non_modal():
        non_modal_msg = AnimatedMessageBox(main_widget)
        non_modal_msg.setWindowTitle("非模态提示")
        non_modal_msg.setText("这条消息将在3秒后自动关闭。")
        non_modal_msg.setIcon(QMessageBox.Information)
        non_modal_msg.showNonModal(3000)

    def show_custom_dialog():
        # Example of using the class directly for more complex dialogs
        dialog = AnimatedMessageBox(main_widget)
        dialog.setWindowTitle("自定义对话框")
        dialog.setText("这是一个可以添加自定义按钮的对话框。")
        dialog.setIcon(QMessageBox.Information)
        custom_button = dialog.addButton("自定义操作", QMessageBox.ActionRole)
        dialog.addButton(QMessageBox.Cancel)
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
