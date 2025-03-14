import glob
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class CommandConfig:
    """Configuration constants for the CommandRunner system.

    This class contains default configuration values and constants used throughout
    the CommandRunner system.

    Attributes:
        DEFAULT_UI_CLASS (str): Default UI class name used when none is specified
        LOG_FORMAT (str): Format string for logging output
    """

    DEFAULT_UI_CLASS = "QAargparseUI"
    LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"


logging.basicConfig(
    level=logging.INFO,
    format=CommandConfig.LOG_FORMAT,
)

CORE_LOGGER = logging.getLogger("CommandRunnerLogger")
CORE_FORMATTER = logging.Formatter(CommandConfig.LOG_FORMAT)


def get_command_config() -> Dict:
    """Get the command configuration dictionary.

    Loads the default configuration and ensures it contains required settings.
    If the default Python interpreter is not in the command list, it will be added.

    Returns:
        Dict: Configuration dictionary containing command settings

    Raises:
        ValueError: If the loaded configuration is not a valid dictionary
    """
    config = load_config("Default")
    if not isinstance(config, Dict):
        raise ValueError("Invalid configuration format")

    config.setdefault("command", [])
    default_py_interpreter = Path(sys.executable).as_posix()

    if default_py_interpreter not in config["command"]:
        config["command"].append(default_py_interpreter)

    return config


def load_config(config_name: str) -> Dict:
    """Load configuration from a JSON file.

    Args:
        config_name (str): Name of the configuration file (without extension)

    Returns:
        Dict: Configuration data loaded from the file. Returns empty dict if file doesn't exist.
    """
    config_data = {}

    config_path = get_config_dir() / f"{config_name}.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            config_data = json.load(f)

    return config_data


def save_config(config_name: str, config_data: dict) -> None:
    """Save configuration data to a JSON file.

    Args:
        config_name (str): Name of the configuration file (without extension)
        config_data (dict): Configuration data to save
    """
    config_path = get_config_dir() / f"{config_name}.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=4)


def add_file_logger(log_path: Path, formatter: logging.Formatter) -> None:
    """Add a file handler to the logger.

    Args:
        log_path (Path): Path to the log file
        formatter (logging.Formatter, optional): Custom formatter for log messages.
            If None, uses the default CORE_FORMATTER.
    """
    if not formatter:
        formatter = CORE_FORMATTER

    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    CORE_LOGGER.addHandler(fh)


def get_logger(name: str = "CommandRunnerLogger") -> logging.Logger:
    """Get a logger instance

    Args:
        name (str): Name of the logger. Defaults to "CommandRunnerLogger"

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    return logger


def get_log_dir() -> Path:
    """Get the path to the log directory.

    Creates the log directory if it doesn't exist.

    Returns:
        Path: Path to the log directory
    """
    directory = Path(__file__).resolve().parent / "log"
    directory.mkdir(exist_ok=True)
    return directory


def get_config_dir() -> Path:
    """Get the path to the configuration directory.

    Creates the config directory if it doesn't exist.

    Returns:
        Path: Path to the configuration directory
    """
    directory = Path(__file__).resolve().parent / "config"
    directory.mkdir(exist_ok=True)
    return directory


def get_commands_map(command_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get a mapping of available commands.

    Scans the commands directory for command modules and creates a mapping of
    command labels to their corresponding classes.

    Args:
        command_path (Path, optional): Custom path to commands directory.
            If None, uses the default Commands directory.

    Returns:
        Dict[str, Any]: Mapping of command labels to command classes
    """
    if not command_path or not isinstance(command_path, Path):
        command_path = Path(__file__).resolve().parent / "Commands"

    commands = {}
    command_files = glob.glob(str(command_path / "Cmd_*.py"))

    for command_file in command_files:
        try:
            command_name = Path(command_file).stem
            module_name = f"Commands.{command_name}"

            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            command_cls = getattr(module, command_name)
            command_instance = command_cls()

            if command_instance.active:
                commands[command_instance.label] = command_instance

        except Exception as e:
            logger = get_logger()
            logger.error(f"Failed to load command {command_file}: {e}", exc_info=True)

    return commands


def generate_html_content_with_links(links, title="", with_votes=True):
    """Generate HTML content with links.

    Args:
        links (list): List of link dictionaries with 'Link', 'Title', and 'Votes' keys
        title (str, optional): Title of the HTML page. Defaults to an empty string.
        with_votes (bool, optional): Include vote counts in the HTML. Defaults to True.

    Returns:
        str: HTML content as a string
    """
    get_logger().info(f"Title = {title}")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    """
    html_content += f"<title>{title}</title>"

    html_content += """
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            h1 {
                font-size: 48px;
                color: #333;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #fff;
                margin: 10px 0;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            a {
                text-decoration: none;
                color: #007bff;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
            .votes {
                color: #555;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
    """
    html_content += f"<h1>{title}</h1>"
    html_content += """
    <ul>
    """

    for link in links:
        try:
            if with_votes:
                html_content += f'<li><a href="{link["Link"]}"> \
                    {link["Title"]}</a> - Votes: {link["Votes"]}</li>'
            else:
                html_content += f'<li><a href="{link["Link"]}">{link["Title"]}</a></li>'

        except Exception as e:
            get_logger().error(f"Exception: {e}")

    html_content += """
        </ul>
    </body>
    </html>
    """

    return html_content


def generate_html_content_with_text(text, title=""):
    """Generate HTML content with text.

    Args:
        text (str): Text content of the HTML page
        title (str, optional): Title of the HTML page. Defaults to an empty string.

    Returns:
        str: HTML content as a string
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    """
    html_content += f"<title>{title}</title>"
    html_content += """
            <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            h1 {
                font-size: 48px;
                color: #333;
            }
            p {
                font-size: 18px;
                color: #333;
            }
        </style>
    </head>
    <body>
    """
    html_content += f"<h1>{title}</h1>"
    html_content += f"<p>{text}</p>"
    html_content += """
    </body>
    </html>
    """

    return html_content
