@echo off
chcp 65001 > nul
cd /d "H:\my_ai"
echo %date% %time% - Starting MyAI application. > startup_log.txt 2>&1

:: Check if pythonw is in PATH
where pythonw >nul 2>&1
if %errorlevel% neq 0 (
    echo %date% %time% - ERROR: pythonw not found in PATH. Please install Python or ensure it's in your PATH. >> startup_log.txt 2>&1
    exit /b 1
)

:: Check if main.py exists
if not exist "main.py" (
    echo %date% %time% - ERROR: main.py not found in H:\my_ai. >> startup_log.txt 2>&1
    exit /b 1
)

:: Run the application
pythonw main.py >> startup_log.txt 2>&1

if %errorlevel% equ 0 (
    echo %date% %time% - MyAI application started successfully. >> startup_log.txt 2>&1
) else (
    echo %date% %time% - ERROR: MyAI application failed to start. >> startup_log.txt 2>&1
) 