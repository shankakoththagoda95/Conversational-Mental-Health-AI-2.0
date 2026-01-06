import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIG
# =========================

MODEL_NAME = "gpt-4o-mini"

CHARACTERS_PATH    = "Characters/characters.json"
PHQ9_QUEST_PATH    = "CommonQuestions/PHQ9.json"
GAD7_QUEST_PATH    = "CommonQuestions/GAD7.json"
ASRM_QUEST_PATH    = "CommonQuestions/ASRM.json"

BASE_CONV_DIR      = "Conversations"
PHQ9_QA_DIR        = os.path.join(BASE_CONV_DIR, "PHQ9", "Question based Conversation")
GAD7_QA_DIR        = os.path.join(BASE_CONV_DIR, "GAD7", "Question based Conversation")
ASRM_QA_DIR        = os.path.join(BASE_CONV_DIR, "ASRM", "Question based Conversation")
CASUAL_DIR         = os.path.join(BASE_CONV_DIR, "Casual")

ROUNDS_PER_CHARACTER = 40  # 40 friend↔persona pairs = 40 turns

# Make folders
for d in [PHQ9_QA_DIR, GAD7_QA_DIR, ASRM_QA_DIR, CASUAL_DIR]:
    os.makedirs(d, exist_ok=True)

# Load env + init client
load_dotenv(Path(__file__).parent / ".env")
client = OpenAI()

# =========================
# UTILITIES
# =========================

def safe_name(s: str) -> str:
    out = "".join(c if c.isalnum() or c in "-_." else "_" for c in s)
    return out.strip("._") or "conversation"

def backoff_sleep(attempt: int):
    time.sleep(1.25 + random.random() * (1.25 + attempt))

def call_chat(messages: List[Dict], temperature: float = 0.7) -> str:
    """Simple wrapper with retry/backoff."""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2:
                return f"[ERROR] {type(e).__name__}: {e}"
            backoff_sleep(attempt)

def load_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]

# =========================
# QUESTIONNAIRE RUNNERS
# =========================

def run_phq9(persona: dict, questions: List[Dict]) -> Dict:
    """
    PHQ-9: 0–3
    Options: Not at all, Several days, More than half the days, Nearly every day
    """
    name = persona["name"]
    system_prompt = persona["system_prompt"]

    results = {"scale": "PHQ9", "character": name, "Common Questions": []}

    option_text = (
        "Please answer briefly and realistically in character.\n"
        "Then on a new line, write: Choice: <one of>\n"
        "Not at all | Several days | More than half the days | Nearly every day."
    )

    for q in questions:
        question = q["content"]
        answer = call_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user",
                 "content": f"{question}\n\n{option_text}"}
            ],
            temperature=0.6,
        )
        results["Common Questions"].append({
            "Consultant": question,
            name: answer
        })

    out_path = os.path.join(PHQ9_QA_DIR, f"{safe_name(name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results

def run_gad7(persona: dict, questions: List[Dict]) -> Dict:
    """
    GAD-7: 0–3
    Same options as PHQ-9.
    """
    name = persona["name"]
    system_prompt = persona["system_prompt"]

    results = {"scale": "GAD7", "character": name, "Common Questions": []}

    option_text = (
        "Please answer briefly and realistically in character.\n"
        "Then on a new line, write: Choice: <one of>\n"
        "Not at all | Several days | More than half the days | Nearly every day."
    )

    for q in questions:
        question = q["content"]
        answer = call_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user",
                 "content": f"{question}\n\n{option_text}"}
            ],
            temperature=0.6,
        )
        results["Common Questions"].append({
            "Consultant": question,
            name: answer
        })

    out_path = os.path.join(GAD7_QA_DIR, f"{safe_name(name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results

def run_asrm(persona: dict, questions: List[Dict]) -> Dict:
    """
    ASRM: 0–4
    Options: Never, Rarely, Sometimes, Often, Very Often
    """
    name = persona["name"]
    system_prompt = persona["system_prompt"]

    results = {"scale": "ASRM", "character": name, "Common Questions": []}

    option_text = (
        "Please answer briefly and realistically in character.\n"
        "Then on a new line, write: Choice: <one of>\n"
        "Never | Rarely | Sometimes | Often | Very Often."
    )

    for q in questions:
        question = q["content"]
        answer = call_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user",
                 "content": f"{question}\n\n{option_text}"}
            ],
            temperature=0.6,
        )
        results["Common Questions"].append({
            "Consultant": question,
            name: answer
        })

    out_path = os.path.join(ASRM_QA_DIR, f"{safe_name(name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results

# =========================
# CASUAL FRIEND CONVERSATION
# =========================

# Paraphrased themes from PHQ-9
PHQ9_TOPICS = [
    "how much you've been enjoying things lately",
    "feeling low, discouraged, or emotionally heavy",
    "how your sleep has been going recently",
    "your energy levels through the day",
    "any changes in how much or how little you're eating",
    "how you’ve been feeling about yourself",
    "whether it's been hard to focus or think clearly",
    "feeling slowed down or unusually restless",
    "if heavy or dark thoughts have been hovering around"
]

# Paraphrased themes from GAD-7
GAD7_TOPICS = [
    "feeling tense or on edge",
    "finding yourself worrying about many different things",
    "whether it's been hard to switch your thoughts off",
    "how easy or hard it is to relax lately",
    "feeling so restless it's hard to sit still",
    "feeling more irritable or snappy than usual",
    "worrying that something bad might happen"
]

# Paraphrased themes from ASRM (activation/mania)
ASRM_TOPICS = [
    "times you might feel unusually upbeat or 'wired'",
    "moments of feeling extra confident or unstoppable",
    "nights where you sleep much less but still feel wired",
    "talking faster or more than usual",
    "taking on lots of projects, spending, or risks"
]

ALL_TOPICS = PHQ9_TOPICS + GAD7_TOPICS + ASRM_TOPICS

def generate_friend_reply(conv_history, next_topic: str) -> str:
    """Friend speaks warmly, 1–2 sentences, guided by topic."""
    transcript = "\n".join(f"{t['role']}: {t['content']}" for t in conv_history[-16:])
    system_prompt = (
        "You are a caring, emotionally intelligent close friend (not a clinician). "
        "You speak in a warm, natural tone, 1–2 short sentences. "
        "You never mention questionnaires, tests, or scales. "
        "You gently explore how your friend is doing (mood, anxiety, energy, sleep, thoughts, behavior) "
        "based on what they said earlier."
    )
    user_message = (
        f"Recent chat:\n{transcript}\n\n"
        f"Next subtle topic to explore: {next_topic}\n"
        f"Respond as the Friend. End with a simple, open question."
    )
    return call_chat(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_message}],
        temperature=0.8
    )

def generate_persona_reply(persona_system_prompt: str, conv_history, friend_msg: str) -> str:
    """Persona replies in character to friend."""
    context = "\n".join(f"{t['role']}: {t['content']}" for t in conv_history[-16:])
    persona_system = (
        f"{persona_system_prompt}\n\n"
        "Reply as yourself to your close friend in 1–3 short, natural sentences. "
        "Be consistent with your personality and previous answers."
    )
    user_message = (
        f"Your friend just said:\n{friend_msg}\n\n"
        f"Recent context:\n{context}\n\n"
        "Now reply as the character."
    )
    return call_chat(
        [{"role": "system", "content": persona_system},
         {"role": "user", "content": user_message}],
        temperature=0.8
    )

def build_background(name: str,
                     phq9: Dict,
                     gad7: Dict,
                     asrm: Dict) -> str:
    """Create short intake-style background from three questionnaires."""
    lines = [f"Intake summary for {name} (from earlier structured questions):"]
    def add_scale(tag, data, limit=6):
        if not data:
            return
        items = data.get("Common Questions", [])
        for row in items[:limit]:
            q = row.get("Consultant", "")
            a = row.get(name, "")
            a = a.replace("\n", " ").strip()
            if not a:
                continue
            lines.append(f"[{tag}] {q} -> {a}")
    add_scale("PHQ9", phq9)
    add_scale("GAD7", gad7)
    add_scale("ASRM", asrm)
    return "\n".join(lines)

def run_casual_conversation(persona: dict,
                            phq9_data: Dict,
                            gad7_data: Dict,
                            asrm_data: Dict) -> Dict:
    """40-turn friend ↔ persona conversation based on all three scales."""
    name = persona["name"]
    persona_system_prompt = persona["system_prompt"]

    background = build_background(name, phq9_data, gad7_data, asrm_data)

    transcript = {
        "character": name,
        "friend_profile": "Caring, supportive close friend (not clinical).",
        "model": MODEL_NAME,
        "turn_limit": ROUNDS_PER_CHARACTER,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "turns": []
    }

    # Initial friend line (personalized using background)
    f0 = call_chat(
        [
            {
                "role": "system",
                "content":
                    "You are a caring close friend. Using the background, open the chat in 1–2 warm sentences. "
                    "Acknowledge they've been going through some things, but DO NOT mention questionnaires or tests."
            },
            {
                "role": "user",
                "content": background
            }
        ],
        temperature=0.7
    )
    transcript["turns"].append({"speaker": "Friend", "text": f0})
    conv_history = [{"role": "Friend", "content": f0}]

    # Persona reply
    p0 = generate_persona_reply(persona_system_prompt, conv_history, f0)
    transcript["turns"].append({"speaker": name, "text": p0})
    conv_history.append({"role": "Persona", "content": p0})

    # Remaining rounds
    for r in range(1, ROUNDS_PER_CHARACTER):
        topic = ALL_TOPICS[r % len(ALL_TOPICS)]

        f_msg = generate_friend_reply(conv_history, topic)
        transcript["turns"].append({"speaker": "Friend", "text": f_msg})
        conv_history.append({"role": "Friend", "content": f_msg})

        p_msg = generate_persona_reply(persona_system_prompt, conv_history, f_msg)
        transcript["turns"].append({"speaker": name, "text": p_msg})
        conv_history.append({"role": "Persona", "content": p_msg})

    transcript["finished_at"] = datetime.utcnow().isoformat() + "Z"

    out_path = os.path.join(CASUAL_DIR, f"{safe_name(name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)

    return transcript

# =========================
# MAIN
# =========================

def main():
    # Load personas
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        personas = json.load(f)["characters"]

    # Load questionnaires
    phq9_questions = load_questions(PHQ9_QUEST_PATH)
    gad7_questions = load_questions(GAD7_QUEST_PATH)
    asrm_questions = load_questions(ASRM_QUEST_PATH)

    print(f"Running for {len(personas)} personas...\n")

    for persona in personas:
        name = persona["name"]
        print(f"--- {name} ---")

        phq9_data = run_phq9(persona, phq9_questions)
        gad7_data = run_gad7(persona, gad7_questions)
        asrm_data = run_asrm(persona, asrm_questions)

        run_casual_conversation(persona, phq9_data, gad7_data, asrm_data)

    print("\n✅ Done.")
    print(f"- PHQ-9 files in: {PHQ9_QA_DIR}")
    print(f"- GAD-7 files in: {GAD7_QA_DIR}")
    print(f"- ASRM files in:  {ASRM_QA_DIR}")
    print(f"- Casual convos:  {CASUAL_DIR}")

if __name__ == "__main__":
    main()
