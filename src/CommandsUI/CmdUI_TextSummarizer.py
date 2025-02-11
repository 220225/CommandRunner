from typing import Dict
from Qt.QtWidgets import (
    QTextEdit,
)

import qargparse.qargparse as qargparse
from .QAargparseUI import QAargparseUI


class TextParagraph(qargparse.QArgument):
    """String type user interface
    Presented by `QtWidgets.QTextEdit`.
    Arguments:
        name (str): The name of argument
        label (str, optional): Display name, convert from `name` if not given
        help (str, optional): Tool tip message of this argument
        default (str, optional): Argument's default value, default None
        placeholder (str, optional): Placeholder message for the widget
        enabled (bool, optional): Whether to enable this widget, default True

    """

    def __init__(self, *args, **kwargs):
        super(TextParagraph, self).__init__(*args, **kwargs)
        self._previous = None

    def isEdited(self):
        return False

    def create(self):
        widget = QTextEdit()

        widget.setMinimumHeight(qargparse.px(300))

        self._read = lambda: widget.toPlainText()
        self._write = lambda value: widget.setText(value)

        if not self._data.get("editable", True):
            widget.setReadOnly(True)

        widget.setPlaceholderText(self._data.get("placeholder") or "")

        initial = self["initial"]

        if initial is None:
            initial = self["default"]

        if initial is not None:
            self._write(initial)
            self._previous = initial

        def read():
            return widget.toPlainText()

        self._read = read

        return widget


class CmdUI_TextSummarizer(QAargparseUI):
    def rebuild_ui(self):
        text_paragraph = TextParagraph(
            "text_paragraph",
            label="Text Paragraph",
            help="Text to summarize",
            placeholder="Enter text to summarize",
        )
        self.ui = qargparse.QArgumentParser([text_paragraph])
        self.ui.changed.connect(self.on_parameter_changed)

    def get_parameters(self) -> Dict:
        parameters = {
            "text_paragraph": self.ui.find("text_paragraph").read(),
        }
        parameters.update(super().get_parameters())
        return parameters