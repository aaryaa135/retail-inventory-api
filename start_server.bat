@echo off
echo ====================================
echo  Starting Retail Inventory API...
echo ====================================
call venv\Scripts\activate.bat
echo.
echo Server starting at: http://localhost:8000
echo API docs at:        http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server.
echo.
uvicorn app.main:app --reload
pause
