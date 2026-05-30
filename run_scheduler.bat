@echo off
echo ========================================
echo   Daily Trading Scheduler
echo ========================================
echo.
echo Starting automated trading scheduler...
echo.
echo Schedule:
echo   - Pre-market: 9:00 AM ET
echo   - Intraday scans: Every 30 min
echo   - Market close: 4:00 PM ET
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd /d "%~dp0"
python daily_scheduler.py

pause