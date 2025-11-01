@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==================================================
REM   Multi-Scale Runner: PHQ-9 / ASRM / GAD-7
REM ==================================================
pushd "%~dp0"

echo.
echo ==========================================
echo   AI Mental Health Scales Runner (Windows)
echo ==========================================
echo.

REM --- 1) Find Python ---
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

REM --- 2) Create venv if missing ---
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PYTHON% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause & exit /b 1
  )
)

REM --- 3) Activate venv ---
call ".venv\Scripts\activate"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  pause & exit /b 1
)

REM --- 4) Upgrade pip (quiet) ---
python -m pip install --upgrade pip >nul

REM --- 5) Install dependencies ---
if exist requirements.txt (
  echo Installing from requirements.txt...
  pip install -r requirements.txt
) else (
  echo Installing required packages...
  pip install openai pandas openpyxl python-dotenv
)

REM --- 6) Ensure OPENAI_API_KEY is set ---
if not defined OPENAI_API_KEY (
  echo.
  set /p OPENAI_API_KEY=Enter your OPENAI_API_KEY sk-... ^> 
  if "!OPENAI_API_KEY!"=="" (
    echo [ERROR] No API key provided. Exiting.
    pause & exit /b 1
  )
  REM Persist for future sessions
  setx OPENAI_API_KEY "!OPENAI_API_KEY!" >nul
  echo Saved OPENAI_API_KEY to your user environment for future runs.
  echo You may need to open a NEW terminal next time to auto-load it.
)

REM --- 7) Ensure folder structure ---
if not exist "PHQ9\Question based Conversation" mkdir "PHQ9\Question based Conversation"
if not exist "PHQ9\Normal Conversation" mkdir "PHQ9\Normal Conversation"
if not exist "ASRM\Question based Conversation" mkdir "ASRM\Question based Conversation"
if not exist "ASRM\Normal Conversation" mkdir "ASRM\Normal Conversation"
if not exist "GAD7\Question based Conversation" mkdir "GAD7\Question based Conversation"
if not exist "GAD7\Normal Conversation" mkdir "GAD7\Normal Conversation"
if not exist "analysis" mkdir "analysis"

REM ==========================
REM           MENU
REM ==========================
:menu
echo.
echo Select an option:
echo   [1] Run PHQ-9 sessions
echo   [2] Run ASRM sessions
echo   [3] Run GAD-7 sessions
echo   [4] Run ALL sessions (PHQ-9 + ASRM + GAD-7)
echo   [5] Run Analysis (if scripts exist)
echo   [Q] Quit
echo.
set /p CHOICE=Enter choice ^> 

if /I "%CHOICE%"=="1" goto run_phq9
if /I "%CHOICE%"=="2" goto run_asrm
if /I "%CHOICE%"=="3" goto run_gad7
if /I "%CHOICE%"=="4" goto run_all
if /I "%CHOICE%"=="5" goto run_analysis
if /I "%CHOICE%"=="Q" goto done
if /I "%CHOICE%"=="q" goto done

echo.
echo [WARN] Invalid choice: %CHOICE%
goto menu

REM ==========================
REM        RUNNERS
REM ==========================
:run_phq9
echo.
echo ==============================
echo   Running PHQ-9 sessions...
echo ==============================
echo.
if exist "run_phq9_sessions.py" (
  python run_phq9_sessions.py
) else (
  echo [ERROR] run_phq9_sessions.py not found in %cd%
)
goto menu

:run_asrm
echo.
echo ==============================
echo   Running ASRM sessions...
echo ==============================
echo.
if exist "run_asrm_sessions.py" (
  python run_asrm_sessions.py
) else (
  echo [ERROR] run_asrm_sessions.py not found in %cd%
)
goto menu

:run_gad7
echo.
echo ==============================
echo   Running GAD-7 sessions...
echo ==============================
echo.
if exist "run_gad7_sessions.py" (
  python run_gad7_sessions.py
) else (
  echo [ERROR] run_gad7_sessions.py not found in %cd%
)
goto menu

:run_all
echo.
echo ==============================
echo   Running ALL sessions...
echo ==============================
echo.

if exist "run_phq9_sessions.py" (
  python run_phq9_sessions.py
) else (
  echo [WARN] run_phq9_sessions.py not found. Skipping PHQ-9.
)

if exist "run_asrm_sessions.py" (
  python run_asrm_sessions.py
) else (
  echo [WARN] run_asrm_sessions.py not found. Skipping ASRM.
)

if exist "run_gad7_sessions.py" (
  python run_gad7_sessions.py
) else (
  echo [WARN] run_gad7_sessions.py not found. Skipping GAD-7.
)

goto menu

REM ==========================
REM        ANALYSIS
REM ==========================
:run_analysis
echo.
echo ==============================
echo   Running analysis exports...
echo ==============================
echo.

REM PHQ-9 analysis (existing)
if exist "analyze_phq9.py" (
  python analyze_phq9.py
) else (
  echo [INFO] analyze_phq9.py not found. Skipping PHQ-9 analysis.
)

REM Normal conversation AI-assisted analysis (optional)
if exist "analyze_normal_conversations_ai.py" (
  python analyze_normal_conversations_ai.py
) else (
  echo [INFO] analyze_normal_conversations_ai.py not found. Skipping normal convo AI analysis.
)

REM If you add ASRM/GAD7 analysis scripts later, they will run here automatically
if exist "analyze_asrm.py" (
  python analyze_asrm.py
) else (
  echo [INFO] analyze_asrm.py not found. Skipping ASRM analysis.
)

if exist "analyze_gad7.py" (
  python analyze_gad7.py
) else (
  echo [INFO] analyze_gad7.py not found. Skipping GAD-7 analysis.
)

echo.
echo ✅ Analysis complete. Files (if generated) are in .\analysis\
goto menu

REM ==========================
REM          EXIT
REM ==========================
:done
echo.
echo ✅ Finished.
echo Outputs live under:
echo   .\PHQ9\Question based Conversation\
echo   .\PHQ9\Normal Conversation\
echo   .\ASRM\Question based Conversation\
echo   .\ASRM\Normal Conversation\
echo   .\GAD7\Question based Conversation\
echo   .\GAD7\Normal Conversation\
echo   .\analysis\
echo.
popd
pause
