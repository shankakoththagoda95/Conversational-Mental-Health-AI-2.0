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
GAD7_QUESTIONS_PATH = "CommonQuestions/GAD7.json"

BASE_GAD7_DIR = "Conversations/GAD7"
GAD7_QA_DIR = os.path.join(BASE_GAD7_DIR, "Question based Conversation")
GAD7_FRIEND_DIR = os.path.join(BASE_GAD7_DIR, "Normal Conversation")

ROUNDS_PER_CHARACTER = 20  # friend↔persona; 20 rounds = 40 utterances total

# Create output dirs
os.makedirs(GAD7_QA_DIR, exist_ok=True)
os.makedirs(GAD7_FRIEND_DIR, exist_ok=True)

# Load .env explicitly and init client
load_dotenv(Path(__file__).parent / ".env")
client = OpenAI()

# Friend paraphrases for GAD-7 topics (kept casual & supportive)
GAD7_PARAPHRASES = [
    "Have you been feeling on edge or tense lately?",
    "Do you ever feel like the worrying just doesn’t switch off?",
    "Have you been worrying about lots of different things at once?",
    "Has it been hard to relax or unwind recently?",
    "Do you feel restless, like it’s tough to sit still?",
    "Have you noticed you’re more irritable than usual?",
    "Do you get that feeling that something bad might happen, even if you can’t say why?"
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
# 1) GAD-7 interview (Q&A)
# -----------------------
def run_gad7_interview(persona: dict, questions: List[Dict]) -> Dict:
    """
    Ask all GAD-7 questions using the persona's system prompt.
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
                        "'Rating: 0–3' (0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day)."
                    )
                }
            ],
            temperature=0.7
        )
        results["Common Questions"].append({
            "Consultant": user_question,
            character_name: answer
        })

    out_path = os.path.join(GAD7_QA_DIR, f"{safe_name(character_name)}.json")
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

def run_friend_conversation_gad7(persona: dict, gad7_transcript: Dict) -> Dict:
    """
    20-round friend↔persona chat seeded with GAD-7 answers.
    """
    character_name = persona["name"]
    persona_system_prompt = persona["system_prompt"]

    # Build background from GAD-7 Q&A
    lines = []
    for row in gad7_transcript["Common Questions"]:
        q = row.get("Consultant", "")
        a = row.get(character_name, "").replace("\n", " ").strip()
        lines.append(f"- Q: {q} | A: {a}")
    background = "What you know from earlier:\n" + "\n".join(lines[:12])

    transcript = {
        "character": character_name,
        "friend_profile": "A caring, supportive close friend who listens and asks gentle questions.",
        "model": MODEL_NAME,
        "turn_limit": ROUNDS_PER_CHARACTER,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "turns": []
    }

    conv_history = [{"role": "Friend", "content": f"Hey, thanks for opening up earlier. {GAD7_PARAPHRASES[0]}"}]

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
        topic = GAD7_PARAPHRASES[r % len(GAD7_PARAPHRASES)]
        f_msg = generate_friend_reply(conv_history, topic)
        transcript["turns"].append({"speaker": "Friend", "text": f_msg})
        conv_history.append({"role": "Friend", "content": f_msg})

        p_msg = generate_persona_reply(persona_system_prompt, conv_history, f_msg)
        transcript["turns"].append({"speaker": character_name, "text": p_msg})
        conv_history.append({"role": "Persona", "content": p_msg})

    transcript["finished_at"] = datetime.utcnow().isoformat() + "Z"

    out_path = os.path.join(GAD7_FRIEND_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)

    return transcript

# -----------------------
# 3) MAIN
# -----------------------
def main():
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        personas = json.load(f)["characters"]
    with open(GAD7_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        gad7_questions = json.load(f)["questions"]

    saved = {"gad7_qa": [], "gad7_friend": []}

    for persona in personas:
        gad_qa = run_gad7_interview(persona, gad7_questions)
        saved["gad7_qa"].append(os.path.join(GAD7_QA_DIR, f"{safe_name(persona['name'])}.json"))

        _ = run_friend_conversation_gad7(persona, gad_qa)
        saved["gad7_friend"].append(os.path.join(GAD7_FRIEND_DIR, f"{safe_name(persona['name'])}.json"))

    print("\n✅ Saved GAD-7 question-based conversations:")
    for p in saved["gad7_qa"]:
        print(f"- {p}")
    print("\n✅ Saved GAD-7 friend conversations:")
    for p in saved["gad7_friend"]:
        print(f"- {p}")

if __name__ == "__main__":
    main()
