@echo off
echo Installing Nova System Control Dependencies...
echo.

echo Installing psutil for system monitoring...
pip install psutil

echo Installing additional Windows support (if on Windows)...
pip install pywin32

echo.
echo System Control Integration Complete!
echo.
echo Available Commands:
echo - Basic (All Users): time, weather, search, open website, system info
echo - Creator Only: open/close apps, system status, volume control, file creation
echo.
echo To test system control, try saying:
echo "What time is it?"
echo "Search for Python tutorials"
echo "What's the weather?"
echo.
pause