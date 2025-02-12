import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

import Core
from Core import CommandConfig

logger = Core.get_logger()


class CommandUIBase:
    """Base class for command user interfaces.

    This class provides the foundation for creating command-specific user
    interface. It defines the basic interface that all command UIs must
    implement.

    Args:
        cmd_cls: The command class instance this UI is associated with
    """

    def __init__(self, cmd_cls):
        self._ui = None
        self._cmd_cls = cmd_cls
        self.rebuild_ui()

    @property
    def ui(self):
        """Get the UI instance.

        Returns:
            The UI instance associated with this command
        """
        return self._ui

    @ui.setter
    def ui(self, value):
        """Set the UI instance.

        Args:
            value: The UI instance to set
        """
        self._ui = value

    def rebuild_ui(self):
        """Rebuild the user interface.

        This method should be implemented by subclasses to create or update
        their specific UI components.

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError(".rebuild_ui() is not defined")

    def get_parameters(self) -> Dict[str, Any]:
        """Get parameters from the UI.

        Returns:
            Dict[str, Any]: Dictionary containing command execution data

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError(".get_parameters() is not defined")

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return f"{type(self).__name__}()"


@dataclass
class CommandBase(ABC):
    """Abstract base class for all commands.

    This class defines the interface that all commands must implement.
    It provides common functionality for UI handling and parameter management.

    Attributes:
        label (str): Display label for the command
        tooltip (str): Tooltip text for the command
        active (bool): Whether the command is active and available for use
        Category (str): Category the command belongs to
        ui_class (str): Name of the UI class to use for this command
    """

    label = ""
    tooltip = ""
    active = True
    Category = "General"
    ui_class = ""

    def __init__(self):
        self._ui_ins = None

    @abstractmethod
    def run(self, data: Dict[str, Any]) -> bool:
        """Execute the command with the given data.

        This method must be implemented by all command subclasses.

        Args:
            data: Dictionary containing command execution data

        Returns:
            bool: True if command executed successfully, False otherwise
        """
        pass

    @property
    def ui(self):
        """Get the command's UI instance.

        Creates the UI if it doesn't exist yet.

        Returns:
            The UI instance for this command
        """
        if not self._ui_ins:
            self.rebuild_ui()

        return self._ui_ins.ui

    def rebuild_ui(self) -> None:
        """Rebuild the command's user interface.

        This method creates or recreates the UI instance for the command,
        using the specified UI class or the default if none is specified.

        Raises:
            AssertionError: If the UI creation fails
            ImportError: If the UI module cannot be imported
        """
        command_ui_module = None
        if not self.ui_class:
            self.ui_class = CommandConfig.DEFAULT_UI_CLASS

        try:
            command_ui_module = importlib.import_module(f"CommandsUI.{self.ui_class}")
            importlib.reload(command_ui_module)
        except ImportError as e:
            logger.error(f"ImportError: {e}", exc_info=True)

        if command_ui_module:
            try:
                ui_cls = getattr(command_ui_module, self.ui_class)
                self._ui_ins = ui_cls(self)
            except Exception as e:
                logger.error("Exception: {0}".format(e), exc_info=True)

        if not self._ui_ins or not self._ui_ins.ui:
            assert False, "UI is not created"

    def get_parameters(self) -> Dict[str, Any]:
        """Get the command's parameters from its UI.

        Returns:
            Dict[str, Any]: Dictionary of parameter names and their values
        """
        return self._ui_ins.get_parameters()
