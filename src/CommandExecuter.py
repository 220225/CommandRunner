import importlib
import json
import os
import timeit
from pathlib import Path

import Core

logger = Core.get_logger()


def execute(ARG_JSON_PATH: str) -> bool:
    """Execute a command using arguments from a JSON file.

    This function handles the execution of commands by:
    1. Loading command arguments from a JSON file
    2. Importing and instantiating the specified command class
    3. Running the command with the provided parameters

    The JSON file should have the following structure:
    {
        "cmd_py_path": "path to the python file contains the command class",
        "param1": "value1",
        "param2": "value2",
        ...
    }

    Args:
        ARG_JSON_PATH (str): Path to the JSON file containing command arguments

    Returns:
        bool: True if command executed successfully, False otherwise

    Raises:
        FileNotFoundError: If the arguments JSON file doesn't exist
        ImportError: If the command module cannot be imported
        ValueError: If the JSON file has invalid format
    """
    try:
        logger.info("arguments_json_path: {0}".format(ARG_JSON_PATH))
        if not Path(ARG_JSON_PATH).exists():
            logger.info("Arguments not existed: {0}".format(ARG_JSON_PATH))
            return False

        with open(ARG_JSON_PATH, "r", encoding="utf-8") as f:
            arg_json_data = json.load(f)

        logger.info("arg_json_data: {0}".format(arg_json_data))
        cmd_py_path = arg_json_data["cmd_py_path"]
        cmd = Path(cmd_py_path).stem

        command_module = None
        try:
            command_module = importlib.import_module(f"Commands.{cmd}")
            importlib.reload(command_module)
        except ImportError as e:
            logger.error(f"ImportError: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error("Exception: {0}".format(e), exc_info=True)
            return False

        if command_module:
            timer_start = timeit.default_timer()
            try:
                command_cls = getattr(command_module, cmd)
                new_command = command_cls()
                new_command.run(arg_json_data)
                timer_end = timeit.default_timer()
                logger.info(
                    "> {0} s, {1} min".format(
                        (timer_end - timer_start), (timer_end - timer_start) / 60.0
                    )
                )
                logger.info("=================================")
                logger.info("")
                return True
            except Exception as e:
                logger.error("Exception: {0}".format(e), exc_info=True)
                return False

        return False

    except Exception as e:
        logger.error(e, exc_info=True)
        return False


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "ARG_JSON_PATH", type=str, help="The path of the arguments json file"
    # )
    # args = parser.parse_args()
    # ARG_JSON_PATH = args.ARG_JSON_PATH
    # execute(ARG_JSON_PATH)

    # NOTE: due to the way blender handles the arguments, currently use environment
    # variable to pass the argument json
    ARG_JSON_PATH = os.environ.get("ARG_JSON_PATH", "")
    execute(ARG_JSON_PATH)
