import logging
import os
from pathlib import Path

from Qt import QtCore, QtGui
from Qt.QtWidgets import QFileDialog, QWidget

import Core
import Util
from CommandBase import CommandUIBase

logger = Core.get_logger()


class FileCollectorWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        Util.load_ui(self)

        # memeber variable
        self._collect_files_model = QtGui.QStandardItemModel(self.file_listView)

        # slot/signal setup
        self.directory_lineEdit.returnPressed.connect(self.build_file_list)
        self.filter_lineEdit.returnPressed.connect(self.build_file_list)
        self.collectFiles_pushButton.clicked.connect(self.build_file_list)
        self.ext_comboBox.currentTextChanged.connect(self.build_file_list)
        self.selectDirectory_pushButton.clicked.connect(self.select_directory)

        self.file_listView.setModel(self._collect_files_model)
        self.file_listView.selectionModel().selectionChanged.connect(
            self.update_selectedFiles_label
        )

        self.loadFiles_pushButton.clicked.connect(
            lambda x: self.save_load_file_list("load")
        )
        self.saveFiles_pushButton.clicked.connect(
            lambda x: self.save_load_file_list("save")
        )

    def collect_target_files(self):
        directory = self.directory_lineEdit.text()
        if not directory:
            return []

        file_filter_list = self.filter_lineEdit.text().split(",")

        file_ext = self.ext_comboBox.currentText()

        all_targets = [
            Path(dp).joinpath(f)
            for dp, dn, filenames in os.walk(directory)
            for f in filenames
            if file_ext == "*.*" or os.path.splitext(f)[1].lower() == file_ext
        ]

        results = []
        matched = 0
        for target in all_targets:
            bFound = False
            for file_filter in file_filter_list:
                if file_filter.lower() in target.as_posix().lower():
                    bFound = True
                    break

            if not bFound:
                continue

            matched += 1
            results.append(target)

        self.update_files_label(len(all_targets), matched)

        return results

    def update_files_label(self, total_files, matched_files):
        self.collectFiles_label.setText(
            f"[{matched_files} / {total_files}] files matched]"
        )
        self.update_selectedFiles_label()

    def update_selectedFiles_label(self, *args):
        current_selected = len(self.file_listView.selectionModel().selectedRows())
        self.selectedFiles_label.setText(f"[{current_selected}] selected")

    def build_file_list(self, *args):
        self._collect_files_model.clear()

        all_targets = self.collect_target_files()
        for target in all_targets:
            item = QtGui.QStandardItem(target.as_posix())

            self._collect_files_model.appendRow(item)

    def select_directory(self, *args):
        dialog = QFileDialog()
        process_dir = dialog.getExistingDirectory(self, "Choose target directory")
        if process_dir:
            self.directory_lineEdit.setText(process_dir)
            self.build_file_list()

    def save_load_file_list(self, mode, *args):
        options = QFileDialog.Options()

        if mode == "save":
            fileName, _ = QFileDialog.getSaveFileName(
                self, "Save File List", "", "*.filelist", options=options
            )
            if not fileName:
                return

            all_targets = self.collect_target_files()
            with open(fileName, "w") as f:
                f.writelines("\n".join([target.as_posix() for target in all_targets]))

        elif mode == "load":
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Open File List", "", "*.filelist", options=options
            )
            if not fileName:
                return

            self._collect_files_model.clear()
            all_targets = []
            with open(fileName, "r") as f:
                for line in f.readlines():
                    target = Path(line.replace("\n", ""))
                    if target.exists():
                        all_targets.append(target)

            for target in all_targets:
                item = QtGui.QStandardItem(target.as_posix())
                self._collect_files_model.appendRow(item)

            self.update_files_label(len(all_targets), 0)

    def get_parameters(self) -> dict:
        return {
            "target_files": self.get_target_files(),
        }

    def get_target_files(self):
        target_files = []
        try:
            indexes = self.file_listView.selectionModel().selectedRows()
            model = self.file_listView.model()
            role = QtCore.Qt.DisplayRole
            for index in indexes:
                target_files.append(model.data(index, role))

        except Exception as e:
            logging.error(e, exc_info=True)

        return target_files


class CmdUI_FileCollector(CommandUIBase):
    def rebuild_ui(self):
        self.ui = FileCollectorWidget()

    def get_parameters(self) -> dict:
        return self.ui.get_parameters()
