import inspect
import json
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from Qt.QtCore import QDir, QProcess, QProcessEnvironment, Qt, Slot
from Qt.QtGui import QColor, QStandardItem, QStandardItemModel, QTextCursor
from Qt.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QPushButton,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import Core
import Util

SUCCESS_COLOR = QColor(92, 184, 92)
FAIL_COLOR = QColor(240, 173, 78)
ERROR_COLOR = QColor(217, 83, 79)
SKIP_COLOR = QColor(88, 165, 204)
NORMAL_COLOR = QColor(200, 200, 200)

STATUS_STR = {
    QProcess.NotRunning: "Not Running",
    QProcess.Starting: "Starting",
    QProcess.Running: "Running",
}
CUR_DIR = Path(__file__).parent

logger = Core.get_logger()


def apply_stylesheet(widget):
    """Apply the application's stylesheet to a widget.

    Args:
        widget: The Qt widget to apply the stylesheet to
    """
    QDir.addSearchPath(
        "icons", Path(__file__).parent.joinpath("ui", "images").as_posix()
    )
    styles_path = Path(__file__).parent.joinpath("style.qss")
    with open(styles_path) as style:
        widget.setStyleSheet(style.read())


class PROCESS_TABLE_HEADER(IntEnum):
    """Enumeration for process table column indices."""

    PROCESS = 0
    PARAMETER = 1
    STDOUT = 2
    STATUS = 3
    KILL = 4
    RUN = 5


class SettingsDialog(QDialog):
    """Dialog for editing application settings.

    This dialog allows users to view and modify the application's configuration
    in JSON format.
    """

    def __init__(self, parent=None):
        """Initialize the settings dialog.

        Args:
            parent: Parent widget
        """
        super(SettingsDialog, self).__init__(parent)

        self.resize(640, 480)
        apply_stylesheet(self)

        layout = QVBoxLayout(self)
        self._output_text_edit = QTextEdit()
        layout.addWidget(self._output_text_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.load_settings()

    def load_settings(self):
        """Load current settings into the text editor."""
        config = Core.get_command_config()
        self._output_text_edit.setPlainText(json.dumps(config, indent=4))

    def accept(self):
        """Handle dialog acceptance.

        Saves the modified configuration and closes the dialog.
        """
        config = json.loads(self._output_text_edit.toPlainText())
        logger.info("config: {0}".format(config))
        Core.save_config("Default", config)
        super(SettingsDialog, self).accept()

    def reject(self):
        """Handle dialog rejection.

        Closes the dialog without saving changes.
        """
        super(SettingsDialog, self).reject()


class LogDialog(QDialog):
    """Dialog for displaying process output logs.

    This dialog shows the output from running processes and maintains
    a maximum buffer size to prevent memory issues.
    """

    def __init__(self, parent=None):
        """Initialize the log dialog.

        Args:
            parent: Parent widget
        """
        super(LogDialog, self).__init__(parent)

        self.resize(640, 480)
        apply_stylesheet(self)

        layout = QVBoxLayout(self)
        self._output_text_edit = QTextEdit()

        self._max_characters = 65535 * 10

        layout.addWidget(self._output_text_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def append_message(self, msg):
        """Append a message to the log.

        Maintains a maximum buffer size by removing old content if necessary.

        Args:
            msg: Message to append
        """
        if len(self._output_text_edit.toPlainText()) > self._max_characters:
            logger.warning(
                "too many output characters [{0}], flush!".format(self._max_characters)
            )
            self._output_text_edit.clear()

        cursor = self._output_text_edit.textCursor()

        if "WARNING" in msg.upper():
            self._output_text_edit.setTextColor(FAIL_COLOR)
        elif "ERROR" in msg.upper() or "EXCEPTION" in msg.upper():
            self._output_text_edit.setTextColor(ERROR_COLOR)
        self._output_text_edit.insertPlainText(msg)
        self._output_text_edit.setTextColor(NORMAL_COLOR)

        cursor.movePosition(QTextCursor.End)
        self._output_text_edit.ensureCursorVisible()


class BatchQProcess(QProcess):
    """Process handler for running commands.

    This class extends QProcess to handle command execution and logging.
    It provides methods for starting processes and handling their output.

    Args:
        _name: Name of the process
        _command: Command to execute
        _script_file: Script file to run
        _arguments: Command arguments
    """

    def __init__(self, _name, _command, _script_file, _arguments):
        QProcess.__init__(self)

        self._name = _name
        self._command = _command
        self._script_file = _script_file
        self._arguments = _arguments

        self._status = ""

        self.build_command_line()

        self._log_dialog = LogDialog()
        self._log_dialog.setWindowTitle(
            "{0}: {1} {2}".format(_name, _script_file, _arguments)
        )

        self._log_dialog.setVisible(False)

    def build_command_line(self):
        """Build the command line for process execution."""
        # simple check for extra arguments
        command_token = self._command.split("--")
        if len(command_token) > 1:
            extra_arguments = "--" + "--".join(command_token[1:])
            self.command_line = '"{0}" {1} "{2}"'.format(
                command_token[0], extra_arguments, self._script_file
            )
        else:
            self.command_line = '"{0}" "{1}"'.format(self._command, self._script_file)
        logger.info("command_line: {0}".format(self.command_line))

        env = QProcessEnvironment.systemEnvironment()
        env.insert(
            "PYTHONPATH",
            CUR_DIR.as_posix() + ";" + env.value("PYTHONPATH"),
        )
        env.insert("ARG_JSON_PATH", self._arguments.as_posix())
        self.setProcessEnvironment(env)

    def do_start(self):
        """Start the process execution."""
        self.start(self.command_line)

    @Slot()
    def show_stdout(self):
        """Show the log dialog with process output."""
        self._log_dialog.setVisible(True)

    @Slot()
    def read_std_out(self):
        """Handle standard output from the process."""
        output_msg = self.readAllStandardOutput()
        output_msg = output_msg.data().decode("ISO-8859-1")
        self._log_dialog.append_message(output_msg)

    @Slot()
    def read_std_error(self):
        """Handle standard error from the process."""
        output_msg = self.readAllStandardError()
        output_msg = output_msg.data().decode("ISO-8859-1")
        self._log_dialog.append_message(output_msg)


class CommandRunnerWidget(QWidget):
    """Main widget for the Command Runner application.

    This widget provides the interface for managing and executing commands.
    It includes a command list, process table, and controls for running
    and managing processes.
    """

    COMMAND_DATA_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        """Initialize the command runner widget.

        Args:
            parent: Parent widget
        """
        QWidget.__init__(self, parent)
        Util.load_ui(self)

        self.refresh_command_btn.clicked.connect(self.build_command_list)

        # member variables
        self._process_list = []
        self._commands_map = {}
        self._commands_model = None
        self._commands_model = QStandardItemModel(self.ui.command_list_view)

        self.build_command_list()
        self.build_executalbe_commands()

        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 2)
        self.ui.command_list_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.command_list_view.selectionModel().selectionChanged.connect(
            self.on_command_selected
        )

        self.add_job_btn.clicked.connect(self.add_process)
        self.delete_job_btn.clicked.connect(lambda: self.remove_selected_process())

        self.process_tableWidget.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

    def build_command_list(self, command_path=None) -> None:
        """Build the list of available commands.

        Args:
            command_path: Optional path to look for commands
        """
        self._commands_map = Core.get_commands_map(command_path)

        self._commands_model.clear()

        for key, item in self._commands_map.items():
            widget_item = QStandardItem(item.label)
            widget_item.setToolTip(item.tooltip)
            widget_item.setData(item, self.COMMAND_DATA_ROLE)
            self._commands_model.appendRow(widget_item)

        self.ui.command_list_view.setModel(self._commands_model)

    def on_command_selected(self, selected, deselected) -> None:
        """Handle command selection.

        Rebuilds the UI for the selected command.

        Args:
            selected: Selected command
            deselected: Deselected command
        """
        Util.clear_layout(self.ui.params_layout)
        for index in selected.indexes():
            command = self.get_command(index)
            command.rebuild_ui()

            self.ui.params_layout.addWidget(command.ui)

    def get_command(self, index):
        """Get the command at the specified index.

        Args:
            index: Index of the command

        Returns:
            Command object
        """
        qt_item = self._commands_model.item(index.row())
        command = qt_item.data(self.COMMAND_DATA_ROLE)
        return command

    def add_process(self, *args):
        """Add a new process to the table.

        Creates a new process and adds it to the table.
        """
        cur_command_index = self.ui.command_list_view.selectedIndexes()
        if not cur_command_index:
            return

        cur_command_index = cur_command_index[0]
        cur_command = self.get_command(cur_command_index)
        cmd_py_path = inspect.getfile(cur_command.__class__)
        if not Path(cmd_py_path).exists():
            logger.error("cmd_py_path not existed: {0}".format(cmd_py_path))
            return

        command = self.command_comboBox.currentText()
        logger.info(f"command: {command}")
        cur_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        arguments_json = Core.get_log_dir() / f"Arguments_{cur_time_str}.json"
        arguments = cur_command.get_parameters()
        arguments["cmd_py_path"] = cmd_py_path

        json.dump(
            arguments,
            open(arguments_json, "w", encoding="utf-8"),
            indent=4,
            ensure_ascii=False,
        )

        executer_py = CUR_DIR / "CommandExecuter.py"

        logger.info(
            f"""add process:
                command: {command},
                exectuer_py_path: {executer_py},
                command_py_path: {cmd_py_path},
                arguments_json: {arguments_json}
            """
        )

        name = "Job #[{0}] ".format(self.process_tableWidget.rowCount())
        self.process_tableWidget.setRowCount(self.process_tableWidget.rowCount() + 1)
        current_row = self.process_tableWidget.rowCount() - 1

        self.c1 = QTableWidgetItem()
        self.c1.setText(name)
        self.process_tableWidget.setItem(
            current_row, PROCESS_TABLE_HEADER.PROCESS, self.c1
        )

        self.c2 = QTableWidgetItem()
        text = "{0} -> {1}".format(cur_command.label, arguments)
        self.c2.setText(text)
        self.c2.setToolTip(text)
        self.process_tableWidget.setItem(
            current_row, PROCESS_TABLE_HEADER.PARAMETER, self.c2
        )

        show_stdout_btn = QPushButton(self.process_tableWidget)
        show_stdout_btn.setText("Show Log")
        self.process_tableWidget.setCellWidget(
            current_row, PROCESS_TABLE_HEADER.STDOUT, show_stdout_btn
        )

        status_item = QTableWidgetItem()
        self.process_tableWidget.setItem(
            current_row, PROCESS_TABLE_HEADER.STATUS, status_item
        )

        kill_btn = QPushButton(self.process_tableWidget)
        kill_btn.setText("")
        self.process_tableWidget.setCellWidget(
            current_row, PROCESS_TABLE_HEADER.KILL, kill_btn
        )

        run_btn = QPushButton(self.process_tableWidget)
        run_btn.setText("Run")
        self.process_tableWidget.setCellWidget(
            current_row, PROCESS_TABLE_HEADER.RUN, run_btn
        )

        process = BatchQProcess(name, command, executer_py, arguments_json)
        process.setProcessChannelMode(QProcess.MergedChannels)

        process.readyReadStandardOutput.connect(process.read_std_out)
        process.readyReadStandardError.connect(process.read_std_error)

        process.stateChanged.connect(
            lambda state: self.handle_stateChanged_cb(state, status_item, kill_btn)
        )
        self.handle_stateChanged_cb(process.state(), status_item, kill_btn)

        process.finished.connect(
            lambda state: self.handle_finished_cb(state, status_item)
        )

        kill_btn.clicked.connect(
            lambda: self.kill_btn_clicked_cb(process, status_item, kill_btn)
        )
        run_btn.clicked.connect(lambda: self.run_btn_clicked_cb(process))

        self.delete_all_job_btn.clicked.connect(self.reset)

        show_stdout_btn.clicked.connect(process.show_stdout)

        self._process_list.append(process)

    def remove_selected_process(self):
        """Remove the selected process from the table.

        Removes the selected process from the table and the process list.
        """
        row = self.process_tableWidget.currentRow()
        if Util.show_yes_no_dialog(
            "Delete Job", f"Are you sure you want to delete job {row}?"
        ):
            self.process_tableWidget.removeRow(row)
            self._process_list.pop(row)

    def reset(self):
        """Reset the process table and list.

        Kills all running processes, clears the table, and resets the process list.
        """
        for p in self._process_list:
            p.kill()

        self._process_list = []
        self.process_tableWidget.clear()
        self.process_tableWidget.setRowCount(0)

    def kill_btn_clicked_cb(self, _process, _status_item, _kill_btn):
        """Handle kill button click.

        Kills the process and updates the status item.

        Args:
            _process: Process to kill
            _status_item: Status item to update
            _kill_btn: Kill button
        """
        _process.kill()
        _kill_btn.setText("Killed")
        _status_item.setText(str(_process.ProcessState))

    def handle_finished_cb(self, state, _status_item):
        """Handle process finished.

        Updates the status item.

        Args:
            state: Process state
            _status_item: Status item to update
        """
        _status_item.setText("Finished!")

    def handle_stateChanged_cb(self, state, _status_item, _kill_btn):
        """Handle process state change.

        Updates the status item and kill button.

        Args:
            state: Process state
            _status_item: Status item to update
            _kill_btn: Kill button to update
        """
        _status_item.setText(STATUS_STR[state])

        if STATUS_STR[state] == "Running":
            _kill_btn.setEnabled(True)
            _kill_btn.setText("Terminated")
        else:
            _kill_btn.setEnabled(False)

    def run_btn_clicked_cb(self, _process):
        """Handle run button click.

        Starts the process.

        Args:
            _process: Process to start
        """
        _process.do_start()

    def open_settings(self):
        """Open the settings dialog.

        Opens the settings dialog and rebuilds the executable commands.
        """
        settings = SettingsDialog()
        settings.exec_()

        self.build_executalbe_commands()

    def build_executalbe_commands(self):
        """Build the executable commands.

        Builds the list of executable commands from the configuration.
        """
        config = Core.get_command_config()
        logger.info("config: {0}".format(config))
        all_commands = config["command"]
        self.command_comboBox.clear()

        for command in all_commands:
            self.command_comboBox.addItem(command)
