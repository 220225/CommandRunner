@echo off
python -m pytest tests/test_core.py -v
if errorlevel 1 (
    echo Test execution failed
    pause
) else (
    echo All tests completed successfully
    pause
)
