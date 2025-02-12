import inspect
import time
from contextlib import ContextDecorator
from pathlib import Path

from Qt import QtCompat, QtWidgets

import Core

logger = Core.get_logger()


def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result

    return wrapper


class elapse_time(ContextDecorator):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        self.time = time.perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        elapsed = time.perf_counter() - self.time
        logger.info(
            f"{self.msg} took {elapsed:.3f} seconds ({elapsed / 60.0:.3f} minutes)"
        )


def ui_path(cls) -> str:
    name = cls.__name__ + ".ui"
    path = inspect.getfile(cls)
    dirname = Path(path).parent

    ui_path = dirname / "resource" / "ui" / name

    if not ui_path.exists():
        ui_path = dirname / "ui" / name

    if not ui_path.exists():
        ui_path = dirname / name

    return ui_path.as_posix()


def load_ui(widget: QtWidgets.QWidget, path=None) -> None:
    if not path:
        path = ui_path(widget.__class__)

    logger.debug("load ui: {0}".format(path))
    try:
        widget.ui = QtCompat.loadUi(path, widget)
    except Exception as e:
        logger.exception(e)


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        child_widget = child.widget()
        if child_widget:
            child_widget.setParent(None)
            child_widget.deleteLater()


def show_yes_no_dialog(title, msg):
    reply = QtWidgets.QMessageBox.question(
        None, title, msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    )
    return reply == QtWidgets.QMessageBox.Yes
