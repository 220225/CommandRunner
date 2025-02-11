# -*- coding: utf_8 -*-
import sys
from contextlib import suppress

with suppress(ModuleNotFoundError):
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CommandRunner")

import qtawesome as qta
from Qt.QtWidgets import QAction, QApplication, QMainWindow

import Core
import Widgets

logger = Core.get_logger()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        config = Core.load_config("Default")
        geometry = config.get("geometry", None)

        if geometry:
            self.set_geometry_settings(geometry)
        else:
            self.resize(640, 480)

        self.setWindowTitle("Command Runner V0.1")
        self.setWindowIcon(qta.icon("ei.asl", color="green"))

        main_widget = Widgets.CommandRunnerWidget()
        self.setCentralWidget(main_widget)

        exit_action = QAction(
            qta.icon("mdi.location-exit", color="white"), "&Exit", self
        )
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)

        setting_action = QAction(
            qta.icon("mdi6.hammer-wrench", color="white"), "&Settings", self
        )
        setting_action.setShortcut("Ctrl+,")
        setting_action.setStatusTip("Open settings")
        setting_action.triggered.connect(self.centralWidget().open_settings)

        menubar = self.menuBar()

        # Add File menu
        menu_file = menubar.addMenu("&File")
        menu_file.addAction(exit_action)
        menu_file.addAction(setting_action)

        self.statusBar()

    def set_geometry_settings(self, settings):
        x, y, width, height = settings

        if QApplication.screens():
            screen_geometry = QApplication.screens()[0].availableGeometry()
            if x > screen_geometry.width() or y > screen_geometry.height():
                x = screen_geometry.center().x()
                y = screen_geometry.center().y()

        self.window().setGeometry(x, y, width, height)

    def closeEvent(self, event):
        config = Core.load_config("Default")
        geometry_settings = (
            self.window().geometry().x(),
            self.window().geometry().y(),
            self.window().geometry().width(),
            self.window().geometry().height(),
        )
        config["geometry"] = geometry_settings
        Core.save_config("Default", config)


def main():
    app = QApplication(sys.argv)

    window = Window()

    window.show()

    Widgets.apply_stylesheet(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
