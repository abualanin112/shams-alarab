@echo off
:: Video Processor Stealth Launcher
:: This script launches the application without showing a console window.

SET VENV_PATH=%~dp0.venv\Scripts\pythonw.exe
SET SCRIPT_PATH=%~dp0main.py

if exist "%VENV_PATH%" (
    start "" "%VENV_PATH%" "%SCRIPT_PATH%"
) else (
    echo [ERROR] Virtual environment not found at %VENV_PATH%
    echo Please ensure the project is set up correctly.
    pause
)

exit
