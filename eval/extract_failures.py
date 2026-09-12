import pandas as pd
pd.set_option('display.max_colwidth', 200)

df = pd.read_csv('eval/eval_results.csv')

intent_wrong = df[df['pred_intent'] != df['gold_intent']]
decision_wrong = df[df['pred_decision'] != df['gold_decision']]

print(f"Total rows: {len(df)}")
print(f"Intent mismatches: {len(intent_wrong)}")
print(f"Decision mismatches: {len(decision_wrong)}")
print()

print("=== INTENT MISMATCHES (sample of 10) ===")
cols = ['text', 'gold_intent', 'pred_intent', 'gold_decision', 'pred_decision']
print(intent_wrong[cols].head(10).to_string())
print()

print("=== DECISION MISMATCHES (sample of 10) ===")
print(decision_wrong[cols].head(10).to_string())
print()

# The most costly kind: auto_send when it shouldn't have been
wrong_auto = df[(df['pred_decision'] == 'auto_send') & (df['gold_decision'] != 'auto_send')]
print(f"=== WRONGFUL AUTO-SEND (highest cost, n={len(wrong_auto)}) ===")
print(wrong_auto[cols].to_string())