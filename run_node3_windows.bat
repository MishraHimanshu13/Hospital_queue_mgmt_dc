@echo off
echo Hospital Queue Management System - Node 3 Setup (Windows)

REM Activate virtual environment
call venv\Scripts\activate

REM Set environment variables
set NODE_ID=node_3
set FLASK_APP=app.py
set FLASK_ENV=development
set SECRET_KEY=change_this_in_production
set DATABASE_URL=postgresql://postgres:postgres@localhost/hospital_queue

echo.
echo Make sure you have already set up the database using the main node script (run_windows.bat).
echo Have you already set up the database with schema and users? (Y/N)
set /p dbready=

if /i not "%dbready%"=="Y" (
    echo Please run the main node script first to set up the database.
    pause
    exit
)

echo Starting the application as Node 3...
python -m flask run --host=0.0.0.0 --port=5002 