@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ——— cd to this script's folder ———
pushd "%~dp0"

echo.
echo ==========================================
echo   AI PHQ-9 + Therapist Runner (Windows)
echo ==========================================
echo.

rem ——— 1) Find Python ———
set "PYTHON="
where py >nul 2>nul && set "PYTHON=py"
if not defined PYTHON (
  where python >nul 2>nul && set "PYTHON=python"
)
if not defined PYTHON (
  echo [ERROR] Python 3.10+ not found. Install from https://www.python.org/downloads/
  pause
  exit /b 1
)

rem ——— 2) Create venv if missing ———
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PYTHON% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause & exit /b 1
  )
)

rem ——— 3) Activate venv ———
call ".venv\Scripts\activate"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  pause & exit /b 1
)

rem ——— 4) Upgrade pip ———
python -m pip install --upgrade pip >nul

rem ——— 5) Install requirements ———
if exist requirements.txt (
  echo Installing from requirements.txt...
  pip install -r requirements.txt
) else (
  echo Installing required packages...
  pip install openai pandas openpyxl python-dotenv
)

rem ——— 6) Ensure OPENAI_API_KEY is set ———
if not defined OPENAI_API_KEY (
  echo.
  set /p OPENAI_API_KEY=Enter your OPENAI_API_KEY sk-... ^> 
  if "!OPENAI_API_KEY!"=="" (
    echo [ERROR] No API key provided. Exiting.
    pause & exit /b 1
  )
  rem Persist for future sessions (won't affect this window)
  setx OPENAI_API_KEY "!OPENAI_API_KEY!" >nul
  echo Saved OPENAI_API_KEY to your user environment for future runs.
  echo You may need to open a NEW terminal next time to auto-load it.
)

rem ——— 7) Ensure output folders ———
if not exist "PHQ9 Conversation" mkdir "PHQ9 Conversation"
if not exist "Normal Conversation" mkdir "Normal Conversation"
if not exist "analysis" mkdir "analysis"

echo.
echo ==============================
echo   Running combined sessions...
echo ==============================
echo.

if exist "run_combined_sessions.py" (
  python run_combined_sessions.py
) else (
  echo [ERROR] run_combined_sessions.py not found in %cd%
  echo Make sure the script is in this folder.
  pause & exit /b 1
)

echo.
echo ==============================
echo   Running analysis exports...
echo ==============================
echo.

if exist "analyze_phq9.py" (
  python analyze_phq9.py
) else (
  echo [WARN] analyze_phq9.py not found. Skipping analysis export.
)

echo.
echo ✅ All done!
echo Outputs:
echo   PHQ9 Conversation\*.json
echo   Normal Conversation\*.json
echo   analysis\phq9_summary.csv / .xlsx
echo   analysis\phq9_detail.csv  / .xlsx
echo.

popd
pause
