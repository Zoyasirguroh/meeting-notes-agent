@echo off
REM Meeting Notes Agent - Stop Script

echo.
echo Stopping Meeting Notes Agent services...
echo.

cd /d "%~dp0"

docker-compose down

echo.
echo Services stopped successfully!
echo.
echo To remove all data and start fresh:
echo   docker-compose down -v
echo.
echo To view what's stopped:
echo   docker ps -a | findstr meeting-notes
echo.

pause
