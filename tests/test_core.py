import pytest
import json
import logging
from unittest.mock import patch
from src.Core import (
    get_command_config,
    load_config,
    save_config,
    get_logger,
    get_log_dir,
    get_config_dir,
    get_commands_map,
    generate_html_content_with_links,
    generate_html_content_with_text,
    add_file_logger,
)


@pytest.fixture
def temp_config_file(tmp_path):
    config_data = {
        "command": ["python.exe"],
        "test_key": "test_value"
    }
    config_file = tmp_path / "Default.json"
    config_file.write_text(json.dumps(config_data))
    return config_file


@pytest.fixture
def temp_commands_dir(tmp_path):
    commands_dir = tmp_path / "Commands"
    commands_dir.mkdir()
    
    # Create a test command file
    cmd_file = commands_dir / "Cmd_Test.py"
    cmd_content = """
class Cmd_Test:
    label = "test"
    active = True
    def __init__(self):
        pass
"""
    cmd_file.write_text(cmd_content)
    return commands_dir


@pytest.fixture
def temp_args_json(tmp_path):
    args_data = {
        "command_name": "Cmd_BlenderDumpSceneInformation",
        "params": {
            "param_output_type": "all",
            "target_files": ["/path/to/test.blend"]
        }
    }
    args_json = tmp_path / "test_args.json"
    args_json.write_text(json.dumps(args_data))
    return args_json


def test_get_logger():
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "CommandRunnerLogger"


def test_get_log_dir():
    log_dir = get_log_dir()
    assert log_dir.exists()
    assert log_dir.is_dir()
    assert log_dir.name == "log"


def test_get_config_dir():
    config_dir = get_config_dir()
    assert config_dir.exists()
    assert config_dir.is_dir()
    assert config_dir.name == "config"


def test_load_and_save_config(tmp_path):
    config_data = {"test_key": "test_value"}
    save_config("test_config", config_data)
    
    loaded_config = load_config("test_config")
    assert loaded_config == config_data


def test_get_command_config(monkeypatch, temp_config_file):
    def mock_load_config(config_name):
        return json.loads(temp_config_file.read_text())
    
    monkeypatch.setattr("src.Core.load_config", mock_load_config)
    
    config = get_command_config()
    assert "command" in config
    assert isinstance(config["command"], list)
    assert all(isinstance(cmd, str) for cmd in config["command"])


def test_get_commands_map(temp_commands_dir):
    commands = get_commands_map(temp_commands_dir)
    assert isinstance(commands, dict)


def test_add_file_logger(tmp_path):
    log_file = tmp_path / "test.log"
    add_file_logger(log_file)
    logger = get_logger()
    
    # Verify the file handler was added
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0
    assert str(log_file) in str(file_handlers[0].baseFilename)


def test_generate_html_content_with_links():
    links = [
        {"Link": "http://example.com", "Title": "Example", "Votes": 10}
    ]
    html = generate_html_content_with_links(links, "Test Title")
    
    assert "Test Title" in html
    assert "http://example.com" in html
    assert "Example" in html
    assert "Votes: 10" in html


def test_generate_html_content_with_links_no_votes():
    links = [
        {"Link": "http://example.com", "Title": "Example"}
    ]
    html = generate_html_content_with_links(links, "Test Title", with_votes=False)
    
    assert "Test Title" in html
    assert "http://example.com" in html
    assert "Example" in html
    assert "Votes:" not in html


def test_generate_html_content_with_text():
    html = generate_html_content_with_text("Test content", "Test Title")
    
    assert "Test Title" in html
    assert "Test content" in html
    assert "<!DOCTYPE html>" in html



@patch('pathlib.Path.exists')
def test_file_collector_wildcard(mock_exists):
    from src.CommandsUI.CmdUI_FileCollector import CmdUI_FileCollector
    
    mock_exists.return_value = True
    collector = CmdUI_FileCollector()
    
    # Test wildcard file extension
    test_files = collector._collect_files("/test/path", "*.*")
    assert isinstance(test_files, list)
    
    # Test specific extension
    test_files = collector._collect_files("/test/path", ".blend")
    assert isinstance(test_files, list)
