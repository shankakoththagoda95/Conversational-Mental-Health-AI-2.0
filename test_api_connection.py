from dotenv import load_dotenv
import os, sys, re
from openai import OpenAI

def clean_key(k: str) -> str:
    # Remove surrounding quotes and whitespace (Windows .env often has them)
    if k is None:
        return ""
    k = k.strip().strip('"').strip("'")
    # Collapse internal whitespace if someone pasted with spaces
    k = re.sub(r"\s+", "", k)
    return k

def die(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)

# 1) Load .env from the script directory explicitly (avoids CWD issues)
from pathlib import Path
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

raw = os.getenv("OPENAI_API_KEY")
key = clean_key(raw)
print(str(key))

if not key:
    die("OPENAI_API_KEY is missing. Put it in a .env file like:\nOPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx")

if not (key.startswith("sk-") or key.startswith("sk-proj-")):
    die(f"OPENAI_API_KEY looks wrong (starts with: {key[:6]}...). It should start with sk- or sk-proj-")

# 2) Initialize client with the sanitized key (instead of relying on env)
client = OpenAI(api_key=key)

# 3) Call a minimal endpoint (chat completion), which is less likely to be restricted
try:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'pong'"}],
        max_tokens=3,
        temperature=0
    )
    print("✅ Chat ok:", resp.choices[0].message.content)
except Exception as e:
    die(f"API call failed: {type(e).__name__}: {e}")
