import logging
from PySide6.QtWidgets import QLabel, QVBoxLayout, QPushButton, QDialogButtonBox, QCheckBox
from PySide6.QtCore import Qt, Signal
from .base_dialog import BaseDialog # Assuming BaseDialog exists for consistent styling

logger = logging.getLogger(__name__)

class AIConsentDialog(BaseDialog):
    """
    A dialog to inform the user about AI feature data usage and obtain consent.
    """
    consent_changed = Signal(bool) # Emits the consent status (True for agreed, False for disagreed)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("启用 AI 增强功能")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("开启 AI 伙伴与智能报告？")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_text = (
            "为了提供 AI 电子宠物互动和个性化善举报告等功能，应用需要将部分数据（例如您的反思文本、活动摘要）"
            "发送给第三方 AI 服务提供商（例如 ZhipuAI）。\n\n"
            "我们致力于保护您的隐私：\n"
            "- **数据最小化:** 仅发送必要信息以实现功能。\n"
            "- **目的明确:** 数据仅用于生成 AI 回应和报告。\n"
            "- **可控性:** 您可以随时在设置中禁用 AI 功能或撤销同意。\n\n"
            "请您放心，您的核心数据（如具体的打卡记录、个人信息）默认存储在本地。\n\n"
            "点击“同意”即表示您理解并同意我们将相关数据用于 AI 功能。如果您不同意，这些 AI 功能将不可用。"
            # TODO: Add links to actual privacy policies when available
            # "\n\n<a href='#'>查看我们的隐私政策</a> | <a href='#'>查看 ZhipuAI 隐私政策</a>"
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText) # Enable link clicking if links are added
        info_label.setOpenExternalLinks(True) # Open links in browser
        layout.addWidget(info_label)

        # Optional: Add a checkbox if you want separate confirmation beyond button click
        # self.confirm_checkbox = QCheckBox("我已阅读并同意上述说明")
        # layout.addWidget(self.confirm_checkbox)

        # Standard Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        agree_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        agree_button.setText("同意并启用")
        disagree_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        disagree_button.setText("暂不同意")

        agree_button.clicked.connect(self.accept_consent)
        disagree_button.clicked.connect(self.reject_consent)

        layout.addWidget(button_box)
        self.setMinimumWidth(400) # Adjust width as needed

    def accept_consent(self):
        """Handles the user agreeing."""
        logger.info("User agreed to AI feature data usage.")
        self.consent_changed.emit(True)
        self.accept() # Close dialog with QDialog.Accepted status

    def reject_consent(self):
        """Handles the user disagreeing."""
        logger.info("User disagreed to AI feature data usage.")
        self.consent_changed.emit(False)
        self.reject() # Close dialog with QDialog.Rejected status

# Example Usage (for testing the dialog itself)
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    dialog = AIConsentDialog()
    result = dialog.exec()

    if result == QDialogButtonBox.StandardButton.Ok: # Or check dialog.result() == QDialog.Accepted
        print("Dialog accepted (User agreed)")
    else:
        print("Dialog rejected or closed (User disagreed)")

    sys.exit()