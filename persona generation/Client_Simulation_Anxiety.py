from openai import OpenAI
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI()

# Define 21 emotional/persona styles ranging from normal to highly paniced
persona_styles = [
    "Sits upright but relaxed, steady breathing, open posture. Eye contact is natural. Speech is measured, even pace, normal volume, few pauses. No fidgeting; facial muscles relaxed.",
    "Slightly more upright posture when listening. Occasionally inhales before answering. Speech normal but slightly brisker when excited. Minimal fingertip fidget (tapping once or twice).",
    "Leaning forward a bit, shoulders slightly tense. Brief micro-pauses before responding as if double-checking. Voice may rise a touch at the end of sentences; blinks slightly more often.",
    "Sits with one leg crossed then uncrossed, small foot tapping. Answers quickly but with a slightly higher pitch. Hands may rub together; breath sometimes shallow.",
    "Frequent small gestures (fiddling with phone, ring). Speech speed increases in short bursts; occasional trailing words. May swallow noticeably and say “um” more often.",
    "Difficulty maintaining steady eye contact for long; glances away while speaking. Chest movements visible (slightly faster respirations). Voice sometimes trembles at sentence start.",
    "Noticeable restlessness: shifts position frequently, taps fingers. Words may clip together (shorter pauses). When asked an open question, takes longer to start answering and may repeat the question.",
    "Speech becomes more verbose but circular (returns to earlier points). Facial musculature tight (jaw clench). May sigh audibly between answers; reports more physical complaints if asked.",
    "Visible sweating, slight hand tremor, hands restless on lap. Answers are shorter when topic is personal; voice sometimes strained. May hold a hand to chest when describing discomfort.",
    "Frequently loses train of thought mid-sentence and backtracks. In conversation, interrupts self to correct worries. Posture hunched; eyes darting slightly",
    "Avoids answering some questions directly; gives generalized answers. Looks down or away during emotional topics. Cry-threatening flushing of eyes may occur (tearing up slightly)",
    "Noticeable tachypnea (fast shallow breaths), fingers white from gripping chair. Speech is faster and sometimes clipped; sentence endings trail off. May press palms together or rub arms",
    "Eyes watering easily, voice cracks on emotional topics, occasional sniffing. Answers may be punctuated by short sobs or the need to pause and collect themselves",
    "Short episodes of hyperventilation when recalling stressful events; hands shaking noticeably. Speech may become pressured in bursts, then slow — breath-driven interruptions",
    "Struggles to complete multi-part answers; loses thread. Appears exhausted; yawns or rubs face often. May decline to elaborate, instead offering terse replies",
    "Rapid speech with rising intonation; words tumble out. Hands gesticulate wildly; may stand or pace briefly even when asked to sit. Eye contact is fleeting and intense",
    "Before questions, shows visible bracing (takes a breath, clenches fists). Answers are dominated by future-oriented “what if” statements. Often interrupts interviewer with worries",
    "Several short panic-like episodes during interaction: sweating, shaking, gasping, stumbling over words. May request to stop or to step outside. Speech can be incoherent briefly",
    "Constant fidgeting and pacing, near-continuous muscle tension. Speech often reduced to short phrases or exclamations. Avoids elaboration; may repeatedly seek reassurance",
    "Appears terrified or frozen at times (freezing posture). Voice is hoarse or whispery from hyperventilation. May cry openly, with difficulty regaining composure; responses may be incoherent",
    "Incapacitated in the interview: unable to sit still, frequent crying, loud sobs, hyperventilation, pleading language (“I can’t…”, “What if…”) and disorganized answers. Requires immediate support; shows inability to verbalize coherent plans"
]

# Base prompt — rewritten to encourage balanced emotional range
base_prompt = """
You are an AI assistant specialized in detailed and unbiased persona generation for conversational simulation between a generated persona and a friend.

Your goal is to generate 63 personas representing a balanced emotional spectrum — from normal and resilient to Debilitating Anxiety . These personas are not all feel anxiety; some are happy, content, or mildly anxiety, while others represent moderate to severe anxiety.

### INSTRUCTIONS ###
1. You will be provided with a persona meta file that has demographic information of a person.
2. Using the provided template, create 63 realistic, specific personas equally distributed across the 21 persona styles (from normal to anxiety).
3. Keep the age and gender proportional to real-world distribution.
4. Each persona should sound natural, relatable, and psychologically realistic.
5. Integrate the given "persona_style" naturally into background, Presenting feelings and thoughts and Demeanor in Simulation.
6. Avoid making every persona sound like a patient — some should be fully healthy individuals.
7. Focus on **life context, personality, and emotional tone**, not just symptoms.
8. IMPORTANT: Place your entire response in the ### PERSONA GENERATION ### section below. Start your response with ’Persona:’ and then provide only the persona description. Do not include any other prefixes, headers, or additional text.
9. Avoid repetition or identical phrasing across personas.


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
Generate 63 personas (Persona 1–63), each corresponding to one persona style listed.
Ensure persona diversity across the set — roughly 3 persona per style.
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
output_file = "anxiety_personas_7.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(personas_text)

print(f"✅ 63 balanced personas saved to {output_file}")
