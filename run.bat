@echo off
REM Convenience script to run UNAGI on Windows
REM Usage: run.bat [arguments]
REM Example: run.bat --simple

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Activate virtual environment
call "%SCRIPT_DIR%venv\Scripts\activate.bat"

REM Run main.py with any arguments passed to this script
python "%SCRIPT_DIR%main.py" %*

@REM Made with Bob
