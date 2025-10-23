import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

MODEL_NAME = "gpt-4o-mini"
CHARACTERS_PATH = "Characters/characters.json"
PHQ9_QUESTIONS_PATH = "CommonQuestions/PHQ9.json"  # your existing PHQ-9 JSON

BASE_PHQ9_DIR = "Conversations/PHQ9"
PHQ9_QA_DIR = os.path.join(BASE_PHQ9_DIR, "Question based Conversation")
PHQ9_FRIEND_DIR = os.path.join(BASE_PHQ9_DIR, "Normal Conversation")

ROUNDS_PER_CHARACTER = 20

os.makedirs(PHQ9_QA_DIR, exist_ok=True)
os.makedirs(PHQ9_FRIEND_DIR, exist_ok=True)

load_dotenv(Path(__file__).parent / ".env")
client = OpenAI()

PHQ9_PARAPHRASES = [
    "Have you still been enjoying the things you used to like doing?",
    "Have you felt down or kind of discouraged lately?",
    "How’s your sleep been—are you sleeping okay or tossing at night?",
    "Have you been feeling low on energy or just tired most of the time?",
    "How’s your appetite these days—eating normally or big changes?",
    "Do you find yourself being too hard on yourself lately?",
    "Has it been harder to concentrate on things like reading or shows?",
    "Have you felt more restless or slower than usual?",
    "Do you ever get thoughts like wishing you weren’t here?"
]

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

def run_phq9_interview(persona: dict, questions: List[Dict]) -> Dict:
    character_name = persona["name"]
    system_prompt = persona["system_prompt"]
    results = {"Common Questions": []}
    for q in questions:
        user_question = q["content"]
        answer = call_chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content":
                    f"{user_question}\n\nPlease answer naturally. You may include a PHQ-9 rating like 'Rating: 0–3' "
                    "(0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day)."}
            ],
            temperature=0.7
        )
        results["Common Questions"].append({"Consultant": user_question, character_name: answer})
    out_path = os.path.join(PHQ9_QA_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results

def generate_friend_reply(conv_history, next_topic_hint: str) -> str:
    transcript = []
    for turn in conv_history[-20:]:
        transcript.append(f"{turn['role']}: {turn['content']}")
    t = "\n".join(transcript).strip()
    system_prompt = (
        "You are a caring close friend (not a clinician). Be warm and brief (1–2 sentences). "
        "Ask about how they’re doing based on what they said earlier."
    )
    user_message = f"Recent chat:\n{t}\n\nNext gentle topic: {next_topic_hint}\nRespond as the Friend."
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
    t = "\n".join(transcript).strip()
    persona_system = f"{persona_system_prompt}\n\nReply to your close friend in 1–3 casual sentences."
    user_message = f"Your friend said: {friend_msg}\n\nContext:\n{t}\n\nReply naturally."
    return call_chat(
        messages=[{"role": "system", "content": persona_system},
                  {"role": "user", "content": user_message}],
        temperature=0.8
    )

def run_friend_conversation_phq9(persona: dict, phq9_transcript: Dict) -> Dict:
    character_name = persona["name"]
    persona_system_prompt = persona["system_prompt"]
    lines = []
    for row in phq9_transcript["Common Questions"]:
        q = row.get("Consultant", "")
        a = row.get(character_name, "").replace("\n", " ").strip()
        lines.append(f"- Q: {q} | A: {a}")
    background = "What you know from earlier:\n" + "\n".join(lines[:12])

    transcript = {
        "character": character_name,
        "friend_profile": "A caring, supportive close friend.",
        "model": MODEL_NAME,
        "turn_limit": ROUNDS_PER_CHARACTER,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "turns": []
    }

    conv_history = [{"role": "Friend", "content": f"Hey, thanks for sharing earlier. {PHQ9_PARAPHRASES[0]}"}]

    f0 = call_chat(
        messages=[
            {"role": "system", "content":
                "You are a caring friend. Use the background to personalize your first message (1–2 warm sentences)."},
            {"role": "user", "content": f"{background}\n\nStart gentle and personal."}
        ],
        temperature=0.7
    )
    transcript["turns"].append({"speaker": "Friend", "text": f0})
    conv_history[-1]["content"] = f0

    p0 = generate_persona_reply(persona_system_prompt, conv_history, f0)
    transcript["turns"].append({"speaker": character_name, "text": p0})
    conv_history.append({"role": "Persona", "content": p0})

    for r in range(1, ROUNDS_PER_CHARACTER):
        topic = PHQ9_PARAPHRASES[r % len(PHQ9_PARAPHRASES)]
        f_msg = generate_friend_reply(conv_history, topic)
        transcript["turns"].append({"speaker": "Friend", "text": f_msg})
        conv_history.append({"role": "Friend", "content": f_msg})

        p_msg = generate_persona_reply(persona_system_prompt, conv_history, f_msg)
        transcript["turns"].append({"speaker": character_name, "text": p_msg})
        conv_history.append({"role": "Persona", "content": p_msg})

    transcript["finished_at"] = datetime.utcnow().isoformat() + "Z"
    out_path = os.path.join(PHQ9_FRIEND_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)
    return transcript

def main():
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        personas = json.load(f)["characters"]
    with open(PHQ9_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    saved = {"phq9_qa": [], "phq9_friend": []}
    for persona in personas:
        phq = run_phq9_interview(persona, questions)
        saved["phq9_qa"].append(os.path.join(PHQ9_QA_DIR, f"{safe_name(persona['name'])}.json"))

        _ = run_friend_conversation_phq9(persona, phq)
        saved["phq9_friend"].append(os.path.join(PHQ9_FRIEND_DIR, f"{safe_name(persona['name'])}.json"))

    print("\n✅ Saved PHQ-9 question-based conversations:")
    for p in saved["phq9_qa"]:
        print(f"- {p}")
    print("\n✅ Saved PHQ-9 friend conversations:")
    for p in saved["phq9_friend"]:
        print(f"- {p}")

if __name__ == "__main__":
    main()
