@echo off
REM Risk Management Diagnostic System - Python Version
REM Shows complete event-to-API trace for debugging risk rules

echo =============================================
echo 🩺 RISK MANAGEMENT DIAGNOSTIC SYSTEM
echo =============================================
echo.
echo This diagnostic system shows you:
echo.
echo 🎯 Which event enums fire
echo    (POSITION_UPDATED, ORDER_FILLED, etc.)
echo.
echo 📦 What payloads are passed
echo    (breach details, position size, symbols)
echo.
echo 🪝 Which hooks trigger
echo    (on_breach, on_trade_executed, etc.)
echo.
echo 🔌 Which API calls are made
echo    (close_position, place_order, etc.)
echo.
echo =============================================
echo.

REM Run the Python diagnostic script
python diagnostic_risk_monitor.py

echo.
echo =============================================
echo 🏁 DIAGNOSTIC SESSION COMPLETE
echo =============================================
echo.
echo Your diagnostic trace has been generated above.
echo Use this to verify your risk rules work correctly!
echo.
pause
