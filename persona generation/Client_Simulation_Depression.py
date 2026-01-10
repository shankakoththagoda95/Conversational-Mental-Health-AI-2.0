from openai import OpenAI
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI()

# Define 27 emotional/persona styles ranging from happy to distressed
persona_styles = [
    "Cheerful, energetic, positive; minor worries but stable mood",
    "Calm, generally happy; brief moments of low motivation",
    "Mostly upbeat, occasional mild fatigue or stress",
    "Balanced; sometimes quiet or tired but optimistic overall",
    "Slight dips in mood, but handles daily life well",
    "Feels fine most days; mild restlessness or irritability at times",
    "Slightly low mood, sometimes distracted or unmotivated",
    "Noticeable sadness some days; energy a bit lower than usual",
    "Feels emotionally drained at times; still social but quieter",
    "Mood often low; needs effort to enjoy normal activities",
    "Feels stressed and self-critical; occasional guilt or frustration",
    "Clearly fatigued; smiles less; energy inconsistent",
    "Flat tone, withdrawn; concentration and interest reduced",
    "Noticeable sadness and lack of motivation; sighs often",
    "Feels stuck or heavy; avoids social activities; pessimistic",
    "Very low energy, self-blame, emotional numbness",
    "Deep sadness; struggles to focus or complete tasks",
    "Frequent hopeless thoughts; speaks slowly, seems tired",
    "Feels trapped or useless; rare moments of relief",
    "Openly distressed; feels life is very hard; tearful or withdrawn",
    "Severe fatigue and hopelessness; may isolate from others",
    "Passive suicidal thoughts possible; very little joy",
    "Emotionally distant; speaks softly; heavy guilt or regret",
    "Deep despair; difficulty getting out of bed or functioning",
    "Feels emotionally empty; strong hopelessness and guilt",
    "Deep psychological pain; may express life feels meaningless",
    "Emotionally collapsed; no motivation or joy; potential suicidal crisis"
]

# Base prompt — rewritten to encourage balanced emotional range
base_prompt = """
You are an AI assistant specialized in detailed and unbiased persona generation for conversational simulation between a generated persona and a friend.

Your goal is to generate 108 personas representing a balanced emotional spectrum — from cheerful and resilient to severely distressed. These personas are not all depressed; some are happy, content, or mildly stressed, while others represent moderate to severe mood difficulties.

### INSTRUCTIONS ###
1. You will be provided with a persona meta file that has demographic information of a person.
2. Using the provided template, create 108 realistic, specific personas equally distributed across the 27 emotional styles (from happy to sad).
3. Keep the age and gender proportional to real-world distribution.
4. Each persona should sound natural, relatable, and psychologically realistic.
5. Integrate the given "Persona Style" naturally into both background and demeanor.
6. Avoid making every persona sound like a patient — some should be fully healthy individuals.
7. Focus on **life context, personality, and emotional tone**, not just symptoms.

### VALUE RANGES AND CATEGORIES ###
ANCESTRY: ["British", "Irish", "German", "Italian", "Polish", "French", "Norwegian", "Dutch", "Swedish", "Other European", "Russian", "Chinese", "Filipino", "Other Asian", "Vietnamese", "Korean", "Japanese", "African", "South American", "Arab", "Oceania"]
HOUSEHOLD_LANGUAGE: [English, Spanish, Swedish, Other Indo-European, Asian/Pacific Islander languages, Other]
EDUCATION: [Less than HS, HS Graduate, Some College, Bachelor’s, Graduate Degree]
EMPLOYMENT_STATUS: [Employed, Unemployed, Not in Labor Force]
CLASS_OF_WORKER: [Private, Government, Self-employed, Unpaid family worker]
INCOME: ["$0-$18,000", "$18,001-$36,000", "$36,001-$72,000", "$72,001-$120,000", "$120,000+"]
MARITAL_STATUS: [Never Married, Married, Divorced, Widowed, Separated]
HOUSEHOLD_TYPE: [Family, Non-family]
DISABILITY: [None, Physical, Mental, Both]

### FINAL PERSONA TEMPLATE ###
{
"Name": "",
"Age": "",
"Gender": "",
"Background": "",
"Education Level": "",
"EDUCATION": "",
"EMPLOYMENT_STATUS": "",
"CLASS_OF_WORKER": "",
"INDUSTRY_CATEGORY": "",
"OCCUPATION_CATEGORY": "",
"INCOME": "",
"MARITAL_STATUS": "",
"HOUSEHOLD_TYPE": "",
"FAMILY_PRESENCE_AND_AGE": "",
"DISABILITY": "",
"Persona Style": "",
"Presenting feelings and thoughts": "",
"Demeanor in Simulation": ""
}

### PERSONA GENERATION ###
Generate 108 personas (Persona 1–108), each corresponding to one emotional style listed.
Ensure emotional diversity across the set — roughly four persona per style.
"""

# Send request to GPT model
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a precise persona generator for conversational simulation."},
        {"role": "user", "content": base_prompt}
    ],
    temperature=0.8
)

# Extract text output
personas_text = response.choices[0].message.content

# Save output
output_file = "balanced_personas1084.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(personas_text)

print(f"✅ 108 balanced personas (happy → sad) saved to {output_file}")
