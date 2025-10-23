import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ========================
# Config
# ========================
MODEL_NAME = "gpt-4o-mini"
CHARACTERS_PATH = "Characters/characters.json"
ASRM_QUESTIONS_PATH = "CommonQuestions/ASRM.json"

BASE_ASRM_DIR = "Conversations/ASRM"
ASRM_QA_DIR = os.path.join(BASE_ASRM_DIR, "Question based Conversation")
ASRM_FRIEND_DIR = os.path.join(BASE_ASRM_DIR, "Normal Conversation")

ROUNDS_PER_CHARACTER = 20  # friend↔persona; 20 rounds = 40 utterances total

# Create output dirs
os.makedirs(ASRM_QA_DIR, exist_ok=True)
os.makedirs(ASRM_FRIEND_DIR, exist_ok=True)

# Load .env explicitly (so it works no matter the working dir)
load_dotenv(Path(__file__).parent / ".env")

# Initialize client (reads OPENAI_API_KEY from env)
client = OpenAI()

# Friend paraphrases for ASRM topics (kept casual & supportive)
ASRM_PARAPHRASES = [
    "Lately have you felt extra upbeat or unusually cheerful?",
    "Do you feel way more confident than usual, sometimes even a bit invincible?",
    "How’s your sleep—do you feel like you need less sleep but still have energy?",
    "Have you noticed yourself talking more or feeling a rush to keep talking?",
    "Have you felt extra active or restless, like you can’t sit still?"
]

# -----------------------
# Utils
# -----------------------
def safe_name(s: str) -> str:
    out = "".join(c if c.isalnum() or c in "-_." else "_" for c in s)
    return out.strip("._") or "conversation"

def backoff_sleep(attempt: int):
    time.sleep(1.25 + random.random() * (1.25 + attempt))

def call_chat(messages: List[Dict], temperature: float = 0.7) -> str:
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == 2:
                return f"[ERROR] {type(e).__name__}: {e}"
            backoff_sleep(attempt)

# -----------------------
# 1) ASRM interview (Q&A)
# -----------------------
def run_asrm_interview(persona: dict, questions: List[Dict]) -> Dict:
    """
    Ask all ASRM questions using the persona's system prompt.
    Return: {"Common Questions": [{ "Consultant": q, "<Name>": answer }, ...]}
    """
    character_name = persona["name"]
    system_prompt = persona["system_prompt"]

    results = {"Common Questions": []}
    for q in questions:
        user_question = q["content"]
        answer = call_chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{user_question}\n\n"
                        "Please answer naturally in your own words. If it fits, include a brief rating like "
                        "'Rating: 0–4' (0=No, 1=Slight, 2=Moderate, 3=Marked, 4=Severe)."
                    )
                }
            ],
            temperature=0.7
        )
        results["Common Questions"].append({
            "Consultant": user_question,
            character_name: answer
        })

    out_path = os.path.join(ASRM_QA_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results

# -----------------------
# 2) Friend conversation
# -----------------------
def generate_friend_reply(conv_history, next_topic_hint: str) -> str:
    transcript = []
    for turn in conv_history[-20:]:
        transcript.append(f"{turn['role']}: {turn['content']}")
    transcript_text = "\n".join(transcript).strip()

    system_prompt = (
        "You are a close friend who genuinely cares and listens well. "
        "You're warm, casual, and supportive — not a therapist. "
        "You remember what the person shared earlier, and you ask about it gently. "
        "Keep replies 1–2 short sentences. Avoid clinical language."
    )
    user_message = (
        f"Recent chat (last turns):\n\n{transcript_text}\n\n"
        f"Next thing to ask about casually: {next_topic_hint}\n\n"
        "Respond as the Friend in 1–2 caring sentences."
    )
    return call_chat(
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_message}],
        temperature=0.8
    )

def generate_persona_reply(persona_system_prompt: str, conv_history, friend_msg: str) -> str:
    transcript = []
    for turn in conv_history[-20:]:
        transcript.append(f"{turn['role']}: {turn['content']}")
    transcript.append(f"Friend: {friend_msg}")
    transcript_text = "\n".join(transcript).strip()

    persona_system = (
        f"{persona_system_prompt}\n\n"
        "Reply as yourself to a trusted friend in a casual, human tone (1–3 sentences). "
        "Be authentic and expressive."
    )
    user_message = (
        f"Your friend just said: {friend_msg}\n\n"
        f"Recent context:\n{transcript_text}\n\n"
        "Reply naturally as yourself."
    )
    return call_chat(
        messages=[{"role": "system", "content": persona_system},
                  {"role": "user", "content": user_message}],
        temperature=0.8
    )

def run_friend_conversation_asrm(persona: dict, asrm_transcript: Dict) -> Dict:
    """
    20-round friend↔persona chat seeded with ASRM answers.
    """
    character_name = persona["name"]
    persona_system_prompt = persona["system_prompt"]

    # Build background from ASRM Q&A
    lines = []
    for row in asrm_transcript["Common Questions"]:
        q = row.get("Consultant", "")
        a = row.get(character_name, "").replace("\n", " ").strip()
        lines.append(f"- Q: {q} | A: {a}")
    background = "What you know from earlier:\n" + "\n".join(lines[:10])

    transcript = {
        "character": character_name,
        "friend_profile": "A caring, supportive close friend who listens and asks gentle questions.",
        "model": MODEL_NAME,
        "turn_limit": ROUNDS_PER_CHARACTER,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "turns": []
    }

    conv_history = [{"role": "Friend", "content": f"Hey, I was thinking about what you said earlier. {ASRM_PARAPHRASES[0]}"}]

    # Friend opener using background
    f0 = call_chat(
        messages=[
            {"role": "system", "content":
                "You are a caring friend. Use the background to make your first message personal and kind. "
                "1–2 sentences; keep it natural."
            },
            {"role": "user", "content": f"{background}\n\nStart with something gentle and personal."}
        ],
        temperature=0.7
    )
    transcript["turns"].append({"speaker": "Friend", "text": f0})
    conv_history[-1]["content"] = f0

    # Persona reply
    p0 = generate_persona_reply(persona_system_prompt, conv_history, f0)
    transcript["turns"].append({"speaker": character_name, "text": p0})
    conv_history.append({"role": "Persona", "content": p0})

    # Continue chat
    for r in range(1, ROUNDS_PER_CHARACTER):
        topic = ASRM_PARAPHRASES[r % len(ASRM_PARAPHRASES)]
        f_msg = generate_friend_reply(conv_history, topic)
        transcript["turns"].append({"speaker": "Friend", "text": f_msg})
        conv_history.append({"role": "Friend", "content": f_msg})

        p_msg = generate_persona_reply(persona_system_prompt, conv_history, f_msg)
        transcript["turns"].append({"speaker": character_name, "text": p_msg})
        conv_history.append({"role": "Persona", "content": p_msg})

    transcript["finished_at"] = datetime.utcnow().isoformat() + "Z"

    out_path = os.path.join(ASRM_FRIEND_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)

    return transcript

# -----------------------
# 3) MAIN
# -----------------------
def main():
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        personas = json.load(f)["characters"]
    with open(ASRM_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        asrm_questions = json.load(f)["questions"]

    saved = {"asrm_qa": [], "asrm_friend": []}

    for persona in personas:
        asrm_qa = run_asrm_interview(persona, asrm_questions)
        saved["asrm_qa"].append(os.path.join(ASRM_QA_DIR, f"{safe_name(persona['name'])}.json"))

        _ = run_friend_conversation_asrm(persona, asrm_qa)
        saved["asrm_friend"].append(os.path.join(ASRM_FRIEND_DIR, f"{safe_name(persona['name'])}.json"))

    print("\n✅ Saved ASRM question-based conversations:")
    for p in saved["asrm_qa"]:
        print(f"- {p}")
    print("\n✅ Saved ASRM friend conversations:")
    for p in saved["asrm_friend"]:
        print(f"- {p}")

if __name__ == "__main__":
    main()
