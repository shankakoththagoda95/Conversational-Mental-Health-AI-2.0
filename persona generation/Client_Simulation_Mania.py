from openai import OpenAI
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI()


# Base prompt — rewritten to encourage balanced emotional range
base_prompt = """
You are an AI assistant specialized in psychological persona generation for conversational simulations.
Your task is to create **50 personas along the mania spectrum**, ranging from **normal mood (no mania)** to **severe mania**.

### GOAL ###
Generate 50 personas that reflect progressive intensities of mania-related behavioural, emotional, and cognitive features, while keeping them realistic and grounded in everyday life.

### INSTRUCTIONS ###
1. You will be provided with demographic metadata and value ranges for features.
2. Create 50 personas (Persona 1–Persona 50), corresponding to these mania levels:

| Persona | Mania Level | Description |
|----------|--------------|-------------|
| 1 | Normal/Euthymic | Stable mood, no abnormal elevation or irritability. |
| 2 | Mild Hypomania | Subtle mood elevation, slightly increased energy and talkativeness. |
| 3 | Moderate Hypomania | Noticeable but functional increase in activity, sleep reduction, confidence. |
| 4 | Full Mania | Marked elevation, decreased need for sleep, impulsivity, grandiosity. |
| 5 | Severe Mania | Extreme and impairing mania with risky behaviours, disorganized thinking. |

3. Maintain given demographic distribution (gender, age, occupation, etc.).
4. Integrate the mania level naturally into **Mood, Sleep, Thought/Speech, and Behaviour** fields and distribute 50 personas equally among all 5 mania levels.
5. Avoid clinical jargon — make each persona sound like a real person with those tendencies.
6. For each persona, fill in the provided JSON template fully and only with relevant values.
7. IMPORTANT: Place your entire response in the ### PERSONA GENERATION ### section below. Start your response with ’Persona:’ and then provide only the persona description. Do not include any other prefixes, headers, or additional text.
8. Avoid repetition or identical phrasing across personas.


### VALUE RANGES AND CATEGORIES ###
ANCESTRY: ["British", "Irish", "German", "Italian", "Polish", "French", "Norwegian", "Dutch", "Swedish", "Other European", "Russian", "Chinese", "Filipino", "Other Asian", "Vietnamese", "Korean", "Japanese", "African", "South American", "Arab", "Oceania"]
HOUSEHOLD_LANGUAGE: [English, Spanish, Swedish, Other Indo-European, Asian/Pacific Islander languages, Other]
EDUCATION: [Less than HS, HS Graduate, Some College, Bachelor’s, Graduate Degree]
EMPLOYMENT_STATUS: [Employed, Unemployed, Not in Labor Force]
CLASS_OF_WORKER: [Private, Government, Self-employed, Unpaid family worker]
INDUSTRY_CATEGORY: [
"Management, business, science, and arts occupations",
"Service occupations",
"Sales and office occupations",
"Natural resources, construction, and maintenance occupations",
"Production, transportation, and material moving occupations"
]
OCCUPATION_CATEGORY: [
"Management, business, science, and arts occupations": [
"Management, business, and financial occupations",
"Computer, engineering, and science occupations",
"Education, legal, community service, arts, and media occupations",
"Healthcare practitioner and technical occupations"
],
"Service occupations": [
"Healthcare support occupations",
"Protective service occupations",
"Food preparation and serving related occupations",
"Building and grounds cleaning and maintenance occupations",
"Personal care and service occupations"
],
"Sales and office occupations": [
"Sales and related occupations",
"Office and administrative support occupations"
],
"Natural resources, construction, and maintenance occupations": [
"Farming, fishing, and forestry occupations",
"Construction and extraction occupations",
"Installation, maintenance, and repair occupations"
],
"Production, transportation, and material moving occupations": [
"Production occupations",
"Transportation occupations",
"Material moving occupations"
]
]
INCOME: ["$0-$18,000", "$18,001-$36,000", "$36,001-$72,000", "$72,001-$120,000", "$120,000+"]
MARITAL_STATUS: [Never Married, Married, Divorced, Widowed, Separated]
HOUSEHOLD_TYPE: [Family, Non-family]
PLACE_OF_BIRTH: [current living country, Foreign Country]
VETERAN_STATUS: [Veteran, Non-veteran]
DISABILITY: [None, Physical, Mental, Both]
HEALTH_INSURANCE: [Private, Public, None]

### PERSONA METADATA ###
{Age distribution: “12-17 years: ~7.1% 
18-24 years: ~7.8% 
25-34 years: ~13.8% 
35-44 years: ~12.8% 
45-54 years: ~12.5% 
55-64 years: ~11.9%
65-74 years: ~10.1%
75+ years (including older than 75): ~10–11%”, 
Gender distribution: “Male population ~50.27%
Female population ~49.73%”}

### PERSONA TEMPLATE ###
{
"Name": "",
"Age": "",
"Gender": "",
"Background": "",
"Education Level": "",
"EMPLOYMENT_STATUS": "",
"CLASS_OF_WORKER": "",
"INDUSTRY_CATEGORY": "",
"OCCUPATION_CATEGORY": "",
"INCOME": "",
"MARITAL_STATUS": "",
"HOUSEHOLD_TYPE": "",
"DISABILITY": "",
"Behavioral Style": "",
"Mood": "",
"Sleep": "",
"Thought, Speech, Cognition": "",
"Behavioural Risk": "",
"Presenting feelings and thoughts": "",
"Demeanor in Simulation": ""
}

### SYMPTOM DOMAINS AND SCALING ###
Scale the following attributes **according to mania intensity**:
- **Mood:** from balanced → mildly elevated → expansive → irritable/euphoric extremes.
- **Sleep:** from normal → slightly reduced → minimal sleep without fatigue.
- **Thought/Speech:** from normal → faster flow → pressured speech, racing thoughts.
- **Behavioural Risk:** from cautious → energetic → impulsive → reckless.
- **Functioning:** from fully stable → mildly affected → severely impaired.

### PERSONA GENERATION ###
Generate 50 personas (Persona 1–50), 10 per mania level.
Each should be distinct, demographically plausible, and psychologically consistent.
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
output_file = "mania_personas_8.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(personas_text)

print(f"✅ 50 balanced personas saved to {output_file}")
