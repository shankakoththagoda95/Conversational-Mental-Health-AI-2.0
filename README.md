


# 🧠 Conversational-Mental-Health-AI-2.0

A GPT-powered experimental environment for studying emotional patterns, depression indicators, and therapeutic communication using simulated characters and PHQ-9 assessment dialogues.
A research-ready conversational AI framework that simulates **mental health assessments** using the **PHQ-9 questionnaire** and follow-up **therapist–persona dialogues**.  
Each persona (e.g., Sherlock Holmes, Jessica Martinez) responds to both the PHQ-9 questions and a natural therapist conversation — allowing analysis of emotional tone, depression indicators, and behavioral patterns.

---

## ✨ Features

- ✅ **PHQ-9 Interview Simulation:** Each persona answers the 9 standard PHQ-9 depression screening questions.
- 🧩 **Therapist Conversation:** A warm, empathetic AI therapist engages in 20-turn natural dialogue with each persona.
- 🧮 **Automatic Scoring:** Fuzzy language analysis converts conversational responses into PHQ-9 numerical scores (0–3 scale).
- 📊 **Export Analysis:** Summaries and detailed tables exported to CSV and Excel for further analysis (SPSS, R, etc.).
- 🧰 **Cross-Platform Runner:** Works on **Windows**, **macOS**, and **Linux** with simple batch/shell scripts.

---

## 🗂️ Project Structure
- Characters/ # Persona profiles (system prompts)
- CommonQuestions/ # PHQ-9 question templates
- PHQ9 Conversation/ # Generated Q&A for each persona
- Normal Conversation/ # Therapist–persona dialogue sessions
- analysis/ # Auto-generated PHQ-9 analysis outputs
- run_combined_sessions.py # Main script: PHQ-9 + therapist combined workflow
- phq9_tools.py # Scoring, summarization, export utilities
- analyze_phq9.py # Runs scoring & exports results
- run_all.bat # Windows batch runner
- run_all.sh # macOS/Linux shell runner
- requirements.txt # Python dependencies


## ⚙️ Setup Instruction

### 1️⃣ Prerequisites

- Python **3.10+**
- An [OpenAI API Key](https://platform.openai.com/account/api-keys)

> 🧠 You **must set your API key** before running any scripts.

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/shankakoththagoda95/Conversational-Mental-Health-AI.git
cd Conversational-Mental-Health-AI
```

🪟 Windows

Run the batch file:

- run_all.bat


🍏 macOS / 🐧 Linux

Make the shell script executable (first time only):
```bash
chmod +x run_all.sh
```
Then run:
```bash
./run_all.sh
```