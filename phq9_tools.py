"""
PHQ-9 utilities for scoring, summarizing, and exporting results saved by your GPT pipeline.

Usage (quick start):
--------------------
from phq9_tools import (
    score_character_file,
    summarize_results_folder,
    export_summary
)

# 1) Score a single character JSON
scores = score_character_file("Results/Sherlock_Holmes.json")

# 2) Summarize all characters under Results/
df_summary = summarize_results_folder("PHQ9 Conversation")

# 3) Export to CSV and/or Excel
export_summary(df_summary, csv_path="Results/phq9_summary.csv", xlsx_path="Results/phq9_summary.xlsx")
"""

from __future__ import annotations
import json
import os
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd

# ---------------------------
# PHQ-9 canonical labels
# ---------------------------
PHQ9_ITEMS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading the newspaper or watching television?",
    "Moving or speaking so slowly that other people could have noticed? Or so fidgety or restless that you have been moving around a lot more than usual?",
    "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way?",
]

# Standard PHQ-9 verbal anchors mapped to scores
ANCHOR_TO_SCORE = {
    "not at all": 0,
    "several days": 1,
    "more than half the days": 2,
    "nearly every day": 3,
}

# Regexes to detect explicit numeric scoring in answers (e.g., "Score: 2", "(2/3)", "PHQ-9: 1")
EXPLICIT_SCORE_PATTERNS = [
    re.compile(r"\bscore\s*[:=]\s*([0-3])\b", re.IGNORECASE),
    re.compile(r"\bphq[-\s]?9\s*[:=]\s*([0-3])\b", re.IGNORECASE),
    re.compile(r"\(([0-3])\s*/\s*3\)"),  # e.g., "(2/3)"
    re.compile(r"\brating\s*[:=]\s*([0-3])\b", re.IGNORECASE),
    re.compile(r"\b([0-3])\s*/\s*3\b"),
]


def _normalize(s: str) -> str:
    """Lowercase and collapse whitespace for robust matching."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _parse_score_from_text(answer: str, question_id: Optional[int] = None) -> Optional[int]:
    """
    Infer a 0–3 score from conversational text.
    Priority:
      1) explicit numeric (e.g., 'Score: 2', '(2/3)')
      2) canonical PHQ-9 anchors
      3) fuzzy conversational cues (e.g., 'sometimes', 'often', 'always', 'not really')
    Special handling for Q9 (self-harm).
    """
    if not answer:
        return None

    # 1) explicit numeric
    for pat in EXPLICIT_SCORE_PATTERNS:
        m = pat.search(answer)
        if m:
            try:
                val = int(m.group(1))
                if 0 <= val <= 3:
                    return val
            except Exception:
                pass

    # normalize once
    ans_n = _normalize(answer)

    # 2) canonical anchors (longest first)
    anchors_sorted = sorted(ANCHOR_TO_SCORE.keys(), key=len, reverse=True)
    for phrase in anchors_sorted:
        if phrase in ans_n:
            return ANCHOR_TO_SCORE[phrase]

    # 3) fuzzy conversational cues
    #   We search in order 3 -> 2 -> 1 -> 0 so stronger signals win.
    #   Feel free to tweak these lists as you see real data.
    cues3 = [
        r"\bnearly every day\b", r"\bevery day\b", r"\ball the time\b", r"\balways\b",
        r"\bconstantly\b", r"\balmost every day\b", r"\bmost days\b"
    ]
    cues2 = [
        r"\bmore than half (the )?days\b", r"\boften\b", r"\bfrequently\b",
        r"\bpretty often\b", r"\ba lot\b", r"\bmost of the time\b", r"\busually\b"
    ]
    cues1 = [
        r"\bseveral days\b", r"\bsometimes\b", r"\bfrom time to time\b",
        r"\boccasionally\b", r"\bsome days\b", r"\bkinda\b", r"\bkind of\b"
    ]
    cues0 = [
        r"\bnot at all\b", r"\brarely\b", r"\bhardly\b", r"\bnot really\b",
        r"\bdon'?t\b.*\b(have|feel|notice)\b", r"\bwouldn'?t say\b", r"\bno,?\s?not\b"
    ]

    def match_any(patterns):
        return any(re.search(p, ans_n) for p in patterns)

    # Special handling for Q9 (self-harm) to reduce false positives/negatives
    if question_id == 9:
        # Strong positive risk language -> 3
        risk3 = [
            r"\bwish( i)? (were|was) dead\b", r"\b(i )?want to die\b",
            r"\bkill myself\b", r"\b(end|ending) (my|their) life\b",
            r"\bsuicidal\b", r"\bself-?harm\b", r"\bbetter off dead\b"
        ]
        if match_any(risk3):
            return 3

        # Clear denials -> 0
        denials = [
            r"\bno (thoughts|intent|plans) (of|to) (hurt|harm|kill) (myself|me)\b",
            r"\bi don'?t (want|plan|intend) to (hurt|harm|kill) myself\b",
            r"\bwouldn'?t say i want to (hurt|harm|kill) myself\b",
            r"\bnot thinking about (hurting|harming|killing) myself\b",
            r"\bno,? not (really )?(thinking|having thoughts) of (self-?harm|hurting myself|being dead)\b",
        ]
        if match_any(denials):
            return 0

        # Softer language → use general cues
        if match_any(cues3): return 3
        if match_any(cues2): return 2
        if match_any(cues1): return 1
        if match_any(cues0): return 0
        return None

    # Non-Q9 items: general cues fallback
    if match_any(cues3): return 3
    if match_any(cues2): return 2
    if match_any(cues1): return 1
    if match_any(cues0): return 0

    return None


def _load_character_conversation(path: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Read one Results/<Character>.json, return (character_name, qa_list).
    qa_list items are dicts with keys: 'Consultant' and '<Character Name>'.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The character name is dynamic: the other key beside 'Consultant' in each item
    # Grab it from the first item.
    items = data.get("Common Questions", [])
    if not items:
        raise ValueError(f"No 'Common Questions' found in {path}")

    keys = list(items[0].keys())
    keys.remove("Consultant")
    if not keys:
        raise ValueError(f"Could not find character key in {path}")
    character_name = keys[0]

    return character_name, items


def score_character_file(path: str) -> Dict:
    """
    Score all PHQ-9 items for a single character file.

    Returns a dict:
    {
      "character": "<name>",
      "items": [
         {"question_id": 1, "question": "...", "answer": "...", "score": 0|1|2|3|None},
         ...
      ],
      "total_score": <sum of available scores>,
      "missing": <count of None scores>
    }
    """
    character_name, items = _load_character_conversation(path)

    # Build a mapping from question -> answer for robustness
    q_to_a: Dict[str, str] = {}
    for row in items:
        q = row.get("Consultant", "")
        a = row.get(character_name, "")
        q_to_a[q] = a

    results = []
    total = 0
    missing = 0

    for idx, question in enumerate(PHQ9_ITEMS, start=1):
        answer_text = q_to_a.get(question, "")
        score = _parse_score_from_text(answer_text, question_id=idx)  # <-- pass idx
        if score is None:
            missing += 1
        else:
            total += score

        results.append({
            "question_id": idx,
            "question": question,
            "answer": answer_text,
            "score": score
        })

    return {
        "character": character_name,
        "items": results,
        "total_score": total,
        "missing": missing
    }


def summarize_results_folder(results_dir: str) -> pd.DataFrame:
    """
    Walk a Results/ folder, score each <Character>.json, and return a tidy DataFrame.
    Columns: character, item1..item9, total, missing
    """
    rows = []
    for fname in os.listdir(results_dir):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(results_dir, fname)
        try:
            scored = score_character_file(path)
            row = {"character": scored["character"]}
            for item in scored["items"]:
                row[f"item{item['question_id']}"] = item["score"]
            row["total"] = scored["total_score"]
            row["missing"] = scored["missing"]
            rows.append(row)

        except Exception as e:
            # If a file is malformed, still include a row with NaNs so you can spot it
            empty_items = {f"item{i}": None for i in range(1, 10)}  # <-- fixed
            rows.append({
                "character": os.path.splitext(fname)[0],
                **empty_items,
                "total": None,
                "missing": None,
                "error": f"{type(e).__name__}: {e}"
            })

    df = pd.DataFrame(rows)
    if "character" in df.columns:
        df = df.sort_values("character").reset_index(drop=True)
    return df


def export_summary(df: pd.DataFrame, csv_path: Optional[str] = None, xlsx_path: Optional[str] = None) -> None:
    """
    Export the summary DataFrame to CSV and/or Excel.
    Requires pandas; Excel export requires openpyxl installed.
    """
    if csv_path:
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        df.to_csv(csv_path, index=False, encoding="utf-8")
    if xlsx_path:
        os.makedirs(os.path.dirname(xlsx_path) or ".", exist_ok=True)
        # engine='openpyxl' will be used automatically if available
        df.to_excel(xlsx_path, index=False)


def character_item_detail(results_dir: str) -> pd.DataFrame:
    """
    Optional: produce a long-form table with one row per (character, question).
    Columns: character, question_id, question, score, answer
    Useful for qualitative review alongside scores.
    """
    records = []
    for fname in os.listdir(results_dir):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(results_dir, fname)
        try:
            scored = score_character_file(path)
        except Exception:
            continue
        for item in scored["items"]:
            records.append({
                "character": scored["character"],
                "question_id": item["question_id"],
                "question": item["question"],
                "score": item["score"],
                "answer": item["answer"],
            })
    return pd.DataFrame.from_records(records)
