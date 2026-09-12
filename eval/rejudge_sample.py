"""
Re-judges the same 20 rows in eval/human_agreement_sample.csv using the
updated, calibrated judge prompt -- lets us check if the fix actually
improves agreement with your human scores WITHOUT re-judging all 166 rows
(saves quota/time). Run this before deciding whether to re-judge the full set.

    python eval/rejudge_sample.py
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from retrieval import build_corpus, retrieve_examples

sys.path.insert(0, os.path.dirname(__file__))
from judge import judge_reply

df = pd.read_csv("eval/human_agreement_sample.csv")
build_corpus("data/comcast_clean_threads.csv")  # no need to exclude golden roots here, judge-only recheck

new_scores = {"grounding": [], "tone": [], "safety": [], "judge_model": []}
for i, row in df.iterrows():
    examples = retrieve_examples(row["text"], n=3)
    scores = judge_reply(row["text"], examples, row["reply"])
    for k in new_scores:
        new_scores[k].append(scores[k])
    print(f"[{i+1}/{len(df)}] grounding={scores['grounding']} tone={scores['tone']} safety={scores['safety']}")

df["grounding"] = new_scores["grounding"]
df["tone"] = new_scores["tone"]
df["safety"] = new_scores["safety"]
df["judge_model"] = new_scores["judge_model"]
df.to_csv("eval/human_agreement_sample.csv", index=False)
print("\nUpdated eval/human_agreement_sample.csv with new judge scores.")
print("Now run: python eval/human_agreement.py")