@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 is not installed.
  echo Download it from: https://www.python.org/downloads/
  echo Select "Add Python to PATH" during installation.
  echo.
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo Social Battery requires Python 3.10 or newer.
  echo Download it from: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Preparing Social Battery for first use...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error

echo.
set /p BUSY_HOST=BUSY Bar IP [10.0.4.20 for USB]: 
echo.

if "%BUSY_HOST%"=="" (
  python social_battery.py
) else (
  python social_battery.py --host "%BUSY_HOST%"
)

if errorlevel 1 goto :error
echo.
pause
exit /b 0

:error
echo.
echo Social Battery stopped with an error. Check the message above.
pause
exit /b 1
