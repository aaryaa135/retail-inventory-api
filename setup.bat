@echo off
echo ====================================
echo  Retail Inventory API - Setup
echo ====================================

echo.
echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found. Install from python.org and tick "Add to PATH"
    pause
    exit /b 1
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 3: Installing packages...
pip install -r requirements.txt

echo.
echo Step 4: Running tests...
python -m pytest app/tests/ -v

echo.
echo ====================================
echo  Setup complete! Now run:
echo  start_server.bat
echo ====================================
pause
