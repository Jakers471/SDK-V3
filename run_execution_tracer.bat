@echo off
REM Execution Flow Tracer - Shows where risk rules go and how hooks execute

echo =============================================
echo 🎯 EXECUTION FLOW TRACER
echo =============================================
echo.
echo This shows EXACTLY where risk rules "go" and how hooks execute:
echo.
echo 🎯 Event fires (POSITION_UPDATED)
echo 🛡️ Risk rule evaluates position size
echo 🚨 Breach detected (size ^> limit)
echo 🪝 Hook executes (on_breach)
echo 🔌 API call made (close_position_direct)
echo ✅ Flow completes with result
echo.
echo =============================================
echo.

REM Run the execution flow tracer
python execution_flow_tracer.py

echo.
echo =============================================
echo 🏁 EXECUTION TRACE COMPLETE
echo =============================================
echo.
echo You now know EXACTLY where risk rules go and how hooks execute!
echo This is the path your 32 risk rules will follow.
echo.
pause
