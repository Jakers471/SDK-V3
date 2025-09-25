@echo off
REM Windows batch file to run event listener and keep terminal open
echo ========================================
echo ProjectX Event Listener with Risk Rules
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the event listener
python event_listener.py

echo.
echo ========================================
echo Event listener session ended
echo ========================================
pause
