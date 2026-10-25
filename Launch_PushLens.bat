@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PUSHLENS_PYTHON=python"
where py >nul 2>nul
if %errorlevel% equ 0 set "PUSHLENS_PYTHON=py -3"
%PUSHLENS_PYTHON% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto missing_python
%PUSHLENS_PYTHON% -m pushlens gui
if errorlevel 1 (
  echo.
  echo PushLens could not start. Check that Python 3.10 or newer includes Tkinter.
  echo See README.md for setup details and other ways to run it.
  pause
  exit /b 1
)
exit /b 0

:missing_python
echo PushLens needs Python 3.10 or newer. Install Python, then reopen this launcher.
echo See README.md for setup details and other ways to run it.
pause
exit /b 1
