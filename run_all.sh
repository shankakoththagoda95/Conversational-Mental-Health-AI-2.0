#!/bin/bash
set -e  # stop on first error

echo ""
echo "=========================================="
echo "   AI PHQ-9 + Therapist Runner (macOS/Linux)"
echo "=========================================="
echo ""

# Move to script directory
cd "$(dirname "$0")"

# ---- 1) Check Python ----
if ! command -v python3 &> /dev/null; then
  echo "[ERROR] Python 3 not found. Please install Python 3.10+."
  echo "Visit: https://www.python.org/downloads/"
  exit 1
fi

# ---- 2) Create virtual environment ----
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# ---- 3) Activate venv ----
source .venv/bin/activate

# ---- 4) Upgrade pip ----
python -m pip install --upgrade pip > /dev/null

# ---- 5) Install requirements ----
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "Installing required packages..."
  pip install openai pandas openpyxl python-dotenv
fi

# ---- 6) Ensure OPENAI_API_KEY is set ----
if [ -z "$OPENAI_API_KEY" ]; then
  echo ""
  read -p "Enter your OPENAI_API_KEY (sk-...): " OPENAI_API_KEY
  if [ -z "$OPENAI_API_KEY" ]; then
    echo "[ERROR] No API key provided. Exiting."
    exit 1
  fi
  # Export for this session only
  export OPENAI_API_KEY="$OPENAI_API_KEY"
  echo "Note: this key will not persist — add it to ~/.bashrc or ~/.zshrc for future runs."
  echo "Example:"
  echo "    export OPENAI_API_KEY=\"$OPENAI_API_KEY\""
  echo ""
fi

# ---- 7) Create folders if missing ----
mkdir -p "PHQ9 Conversation" "Normal Conversation" "analysis"

echo ""
echo "=============================="
echo " Running combined sessions..."
echo "=============================="
echo ""

if [ -f "run_combined_sessions.py" ]; then
  python run_combined_sessions.py
else
  echo "[WARN] run_combined_sessions.py not found!"
  exit 1
fi

echo ""
echo "=============================="
echo " Running analysis exports..."
echo "=============================="
echo ""

if [ -f "analyze_phq9.py" ]; then
  python analyze_phq9.py
else
  echo "[WARN] analyze_phq9.py not found. Skipping analysis."
fi

echo ""
echo "✅ All done!"
echo "Outputs saved to:"
echo "  - PHQ9 Conversation/*.json"
echo "  - Normal Conversation/*.json"
echo "  - analysis/phq9_summary.csv/.xlsx"
echo ""
