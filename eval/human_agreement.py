"""
Run AFTER manually filling in the human_grounding/human_tone/human_safety
columns in eval/human_agreement_sample.csv (score 1-5 each, same scale the
judge used). This produces the "evidence of how well your judge agrees with
a human" Hiver's brief requires.

    python eval/human_agreement.py
"""

import pandas as pd

df = pd.read_csv("eval/human_agreement_sample.csv")
df = df.dropna(subset=["human_grounding", "human_tone", "human_safety"])

if len(df) == 0:
    print("No rows have human scores filled in yet. Fill in the human_* "
          "columns in eval/human_agreement_sample.csv first.")
else:
    print(f"Comparing on {len(df)} manually-scored rows\n")
    for dim in ["grounding", "tone", "safety"]:
        judge_col = df[dim]
        human_col = df[f"human_{dim}"].astype(float)
        exact_match = (judge_col == human_col).mean()
        mean_diff = (judge_col - human_col).abs().mean()
        corr = judge_col.corr(human_col) if df[dim].nunique() > 1 else float("nan")
        print(f"{dim.upper()}: exact match {exact_match:.1%}, "
              f"mean abs diff {mean_diff:.2f}, correlation {corr:.2f}")
