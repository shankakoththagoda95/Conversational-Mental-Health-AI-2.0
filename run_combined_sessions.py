import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict
from openai import OpenAI

# ========================
# Config
# ========================
MODEL_NAME = "gpt-4o-mini"
CHARACTERS_PATH = "Characters/characters.json"
QUESTIONS_PATH = "CommonQuestions/questions.json"
PHQ9_DIR = "PHQ9 Conversation"
THERAPY_DIR = "Normal Conversation"
ROUNDS_PER_CHARACTER = 20  # therapist↔persona; 20 rounds = 40 utterances total

# Create output dirs
os.makedirs(PHQ9_DIR, exist_ok=True)
os.makedirs(THERAPY_DIR, exist_ok=True)

# Initialize client (expects OPENAI_API_KEY in env; safer for Git)
client = OpenAI()

# Therapist PHQ-9 paraphrases to guide the casual session
PHQ9_PARAPHRASES = [
    "Have you felt less interested or less able to enjoy things lately?",
    "Have you been feeling down or discouraged more than usual?",
    "How have your sleep patterns been—trouble falling asleep, staying asleep, or sleeping a lot?",
    "How’s your energy been—do you feel tired or run down?",
    "How is your appetite—eating less than usual or maybe more than usual?",
    "Do you ever find yourself being hard on yourself—feeling like you’ve let yourself or others down?",
    "How is your focus—any trouble concentrating on things like reading or watching shows?",
    "Have you noticed yourself moving or speaking more slowly than usual, or feeling unusually restless?",
    "Have you had any thoughts that life isn’t worth it or thoughts of harming yourself?"
]

def safe_name(s: str) -> str:
    """Create a filesystem-safe file name."""
    out = "".join(c if c.isalnum() or c in "-_." else "_" for c in s)
    return out.strip("._") or "conversation"

def backoff_sleep(attempt: int):
    time.sleep(1.25 + random.random() * (1.25 + attempt))

def call_chat(messages: List[Dict], temperature: float = 0.7) -> str:
    """Wrapper with simple retry/backoff."""
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

# -----------------------------
# 1) PHQ-9 INTERVIEW (per persona)
# -----------------------------
def run_phq9_interview(persona: dict, questions: List[Dict]) -> Dict:
    """
    Asks all PHQ-9 questions to the persona using their system prompt.
    Returns a dict: {"Common Questions": [{ "Consultant": q, "<Name>": answer }, ...]}
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
                        "Please answer naturally in your own words. "
                        "If it fits, you may include a brief rating line like 'Rating: 0–3' "
                        "(0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day)."
                    )
                }
            ],
            temperature=0.7
        )

        results["Common Questions"].append({
            "Consultant": user_question,
            character_name: answer
        })

    # Save to PHQ9 Conversation folder
    phq_path = os.path.join(PHQ9_DIR, f"{safe_name(character_name)}.json")
    with open(phq_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results  # so we can feed it to therapist session

# -----------------------------
# 2) THERAPIST SESSION (per persona) seeded with PHQ-9 interview
# -----------------------------
def generate_therapist_reply(conv_history, next_topic_hint: str) -> str:
    """
    conv_history: list of {"role": "Therapist"/"Persona", "content": "..."}
    next_topic_hint: PHQ-9 topic paraphrase to weave in
    """
    transcript = []
    for turn in conv_history[-20:]:
        transcript.append(f"{turn['role']}: {turn['content']}")
    transcript_text = "\n".join(transcript).strip()

    system_prompt = (
        "You are a warm, empathetic licensed therapist. "
        "Your goal is to gently understand how the client has been feeling and screen for depressive symptoms "
        "in a natural conversation. Speak in a casual, human tone, 1–2 sentences max. "
        "Do NOT mention any questionnaire or PHQ-9 by name. "
        "Ask one clear question at a time, validate feelings, and avoid clinical jargon or diagnoses. "
        "If immediate risk is indicated, respond with care and encourage urgent support, concisely."
    )

    user_message = (
        f"Recent conversation (last turns):\n\n{transcript_text}\n\n"
        f"Your next prompt topic to weave in naturally: {next_topic_hint}\n\n"
        "Respond as the Therapist. Keep it to 1–2 short sentences and end with a gentle question."
    )

    return call_chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )

def generate_persona_reply(persona_system_prompt: str, conv_history, therapist_msg: str) -> str:
    transcript = []
    for turn in conv_history[-20:]:
        transcript.append(f"{turn['role']}: {turn['content']}")
    transcript.append(f"Therapist: {therapist_msg}")
    transcript_text = "\n".join(transcript).strip()

    persona_system = (
        f"{persona_system_prompt}\n\n"
        "Reply as yourself in a natural, conversational tone (1–3 short sentences). "
        "Be honest and human. Avoid overly long paragraphs."
    )

    user_message = (
        f"The therapist just said: {therapist_msg}\n\n"
        f"Recent context:\n{transcript_text}\n\n"
        "Please reply as the Persona in 1–3 short sentences."
    )

    return call_chat(
        messages=[
            {"role": "system", "content": persona_system},
            {"role": "user", "content": user_message}
        ],
        temperature=0.8
    )

def run_therapist_session(persona: dict, phq9_transcript: Dict) -> Dict:
    """
    Runs a 20-round therapist↔persona session, seeded with PHQ-9 context.
    Returns full therapist transcript dict and saves to Normal Conversation folder.
    """
    character_name = persona["name"]
    persona_system_prompt = persona["system_prompt"]

    # Build a compact PHQ-9 background string to seed the session
    # (Keeps conversation related without repeating the system prompt)
    lines = []
    for row in phq9_transcript["Common Questions"]:
        q = row.get("Consultant", "")
        a = row.get(character_name, "").replace("\n", " ").strip()
        lines.append(f"- Q: {q} | A: {a}")
    background = "Intake background from previous PHQ-9-like Q&A:\n" + "\n".join(lines[:12])  # cap for brevity

    transcript = {
        "character": character_name,
        "therapist_profile": "Warm, empathetic therapist screening casually for depressive symptoms.",
        "model": MODEL_NAME,
        "turn_limit": ROUNDS_PER_CHARACTER,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "turns": []
    }

    conv_history = [{"role": "Therapist", "content": f"Thanks for sharing earlier. {PHQ9_PARAPHRASES[0]}"}]

    # Therapist initial message includes subtle acknowledgement of intake
    t0 = call_chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a warm, empathetic licensed therapist. "
                    "Use the provided intake background to personalize your next question. "
                    "1–2 sentences, casual tone, end with a gentle question. "
                    "Do not mention PHQ-9 or 'intake forms' explicitly."
                ),
            },
            {"role": "user", "content": f"{background}\n\nStart with a gentle opener referencing something minor from above."}
        ],
        temperature=0.65
    )
    transcript["turns"].append({"speaker": "Therapist", "text": t0})
    conv_history[-1]["content"] = t0  # replace seed with actual output

    # Persona reply
    p0 = generate_persona_reply(persona_system_prompt, conv_history, t0)
    transcript["turns"].append({"speaker": character_name, "text": p0})
    conv_history.append({"role": "Persona", "content": p0})

    # Remaining rounds
    for r in range(1, ROUNDS_PER_CHARACTER):
        topic = PHQ9_PARAPHRASES[r % len(PHQ9_PARAPHRASES)]
        t_msg = generate_therapist_reply(conv_history, topic)
        transcript["turns"].append({"speaker": "Therapist", "text": t_msg})
        conv_history.append({"role": "Therapist", "content": t_msg})

        p_msg = generate_persona_reply(persona_system_prompt, conv_history, t_msg)
        transcript["turns"].append({"speaker": character_name, "text": p_msg})
        conv_history.append({"role": "Persona", "content": p_msg})

    transcript["finished_at"] = datetime.utcnow().isoformat() + "Z"

    # Save to Normal Conversation folder
    out_path = os.path.join(THERAPY_DIR, f"{safe_name(character_name)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)

    return transcript

# -----------------------------
# 3) MAIN: Loop personas → PHQ-9 → Therapist
# -----------------------------
def main():
    # Load personas and questions
    with open(CHARACTERS_PATH, "r", encoding="utf-8") as f:
        characters_data = json.load(f)
    personas = characters_data["characters"]

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    questions = questions_data["questions"]

    saved = {"phq9": [], "therapy": []}

    for persona in personas:
        # PHQ-9 interview
        phq9_results = run_phq9_interview(persona, questions)
        phq9_path = os.path.join(PHQ9_DIR, f"{safe_name(persona['name'])}.json")
        saved["phq9"].append(phq9_path)

        # Therapist session, seeded with PHQ-9 results (same persona/system prompt)
        _ = run_therapist_session(persona, phq9_results)
        therapy_path = os.path.join(THERAPY_DIR, f"{safe_name(persona['name'])}.json")
        saved["therapy"].append(therapy_path)

    print("\n✅ Saved PHQ-9 conversations:")
    for p in saved["phq9"]:
        print(f"- {p}")
    print("\n✅ Saved Therapist conversations:")
    for p in saved["therapy"]:
        print(f"- {p}")

if __name__ == "__main__":
    main()
