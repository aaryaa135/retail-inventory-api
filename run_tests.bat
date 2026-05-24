@echo off
echo ====================================
echo  Running all 40 tests...
echo ====================================
call venv\Scripts\activate.bat
python -m pytest app/tests/ -v
pause
