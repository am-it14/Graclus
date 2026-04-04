@echo off
REM ============================================================
REM  start_all.bat  —  Starts backend + frontend together
REM  Run from PROJECT_X\ root directory
REM ============================================================

echo.
echo ============================================================
echo  ExamCluster — Starting all services
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo [1/4] Installing Python backend dependencies...
cd backend
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Installing frontend Node dependencies (if needed)...
cd ..\user_exp
if not exist node_modules (
    npm install
)

echo.
echo [3/4] Starting FastAPI backend on http://localhost:8000 ...
cd ..\backend
start "ExamCluster Backend" cmd /k "uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [4/4] Starting React frontend on http://localhost:5173 ...
cd ..\user_exp
start "ExamCluster Frontend" cmd /k "npm run dev"

echo.
echo ============================================================
echo  All services started!
echo.
echo  Frontend:  http://localhost:5173
echo  Backend:   http://localhost:8000
echo  API docs:  http://localhost:8000/docs
echo ============================================================
echo.
pause
