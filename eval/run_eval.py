"""
Full evaluation harness. Run from the project root:

    python eval/run_eval.py [--limit N] [--skip-judge]

Produces:
- eval/eval_results.csv          -- per-row predictions vs golden labels
- eval/human_agreement_sample.csv -- 20-row sample for manual judge-agreement check
- console summary: intent accuracy, decision accuracy, cost-weighted
  decision score, judge scores (by judge_model), vs both baselines
"""

import argparse
import os
import sys
import random
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from retrieval import build_corpus, retrieve_examples
from classify import classify
from draft import draft_reply
from decide import decide

sys.path.insert(0, os.path.dirname(__file__))
from baselines import trivial_baseline, simple_baseline
from judge import judge_reply

# Cost weights for decision mismatches, tied directly to the Aim: a wrong
# auto-send on something that needed escalation is the worst possible
# error (brand damage); a wrong escalate on something that could've been
# auto-sent just costs a little human review time.
DECISION_COST = {
    ("auto_send", "escalate_priority"): 5,   # worst: auto-sent something that needed urgent escalation
    ("auto_send", "draft_hold"): 3,          # bad: auto-sent something needing review
    ("draft_hold", "escalate_priority"): 1,  # minor: under-prioritized, still human-reviewed
    ("escalate_priority", "draft_hold"): 0.5,# minor: over-prioritized, safe direction
}


def cost(predicted, actual):
    if predicted == actual:
        return 0
    return DECISION_COST.get((predicted, actual), 1)  # default mid cost for other mismatches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="eval/golden_set.csv")
    parser.add_argument("--corpus", default="data/comcast_clean_threads.csv")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-judge", action="store_true",
                         help="Skip LLM-judge scoring to save API quota/time")
    parser.add_argument("--output", default="eval/eval_results.csv")
    args = parser.parse_args()

    golden = pd.read_csv(args.golden)
    golden = golden[golden["intent"] != "unlabeled_needs_review"].copy()
    if args.limit:
        golden = golden.head(args.limit)

    # resume support: skip rows already in a previous (possibly crashed) run
    done_ids = set()
    if os.path.exists(args.output):
        done_ids = set(pd.read_csv(args.output)["tweet_id"].astype(str))
        print(f"Resuming -- {len(done_ids)} rows already done, skipping those.\n")
    golden = golden[~golden["tweet_id"].astype(str).isin(done_ids)]

    print(f"Evaluating on {len(golden)} remaining golden-set examples\n")

    # exclude golden-set threads from the retrieval corpus -- prevents the
    # system from retrieving its own answer (decision_log.md #13)
    n_pairs = build_corpus(args.corpus, exclude_roots=set(golden["root"]))
    print(f"Retrieval corpus (golden threads excluded): {n_pairs} pairs\n")

    results = []
    for i, row in golden.iterrows():
        text, gold_intent, gold_decision = row["text"], row["intent"], row["decision"]

        pred_intent, classify_model = classify(text)
        trivial_intent, trivial_decision = trivial_baseline(text)
        simple_intent, simple_decision = simple_baseline(text)

        record = {
            "tweet_id": row["tweet_id"], "text": text,
            "gold_intent": gold_intent, "gold_decision": gold_decision,
            "pred_intent": pred_intent, "classify_model": classify_model,
            "trivial_intent": trivial_intent, "trivial_decision": trivial_decision,
            "simple_intent": simple_intent, "simple_decision": simple_decision,
        }

        if pred_intent in ("off_topic", "venting"):
            record["pred_decision"] = (
                "filtered_off_topic" if pred_intent == "off_topic" else "hold_low_priority"
            )
            record["reply"] = None
        else:
            examples = retrieve_examples(text, n=3)
            reply, draft_model = draft_reply(text, examples)
            pred_decision = decide(pred_intent, text)
            record["pred_decision"] = pred_decision
            record["reply"] = reply
            record["draft_model"] = draft_model

            if not args.skip_judge:
                scores = judge_reply(text, examples, reply)
                record.update(scores)

        record["decision_cost"] = cost(record["pred_decision"], gold_decision)
        results.append(record)
        print(f"[{i+1}/{len(golden)}] gold={gold_intent}/{gold_decision}  "
              f"pred={pred_intent}/{record['pred_decision']}")

        pd.DataFrame([record]).to_csv(
            args.output, mode="a", header=not os.path.exists(args.output), index=False
        )

    df = pd.read_csv(args.output)  # reload full accumulated results (incl. resumed rows), not just this session's

    intent_acc = (df["pred_intent"] == df["gold_intent"]).mean()
    decision_acc = (df["pred_decision"] == df["gold_decision"]).mean()
    trivial_intent_acc = (df["trivial_intent"] == df["gold_intent"]).mean()
    trivial_decision_acc = (df["trivial_decision"] == df["gold_decision"]).mean()
    simple_intent_acc = (df["simple_intent"] == df["gold_intent"]).mean()
    simple_decision_acc = (df["simple_decision"] == df["gold_decision"]).mean()
    avg_cost = df["decision_cost"].mean()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Shivika   intent accuracy: {intent_acc:.2%}  | decision accuracy: {decision_acc:.2%}")
    print(f"Trivial   intent accuracy: {trivial_intent_acc:.2%}  | decision accuracy: {trivial_decision_acc:.2%}")
    print(f"Simple    intent accuracy: {simple_intent_acc:.2%}  | decision accuracy: {simple_decision_acc:.2%}")
    print(f"Average decision cost (0=perfect, higher=worse): {avg_cost:.3f}")

    if not args.skip_judge and "judge_model" in df.columns:
        judged = df.dropna(subset=["judge_model"])
        for model in judged["judge_model"].unique():
            sub = judged[judged["judge_model"] == model]
            print(f"\nJudge scores (judge_model={model}, n={len(sub)}):")
            print(f"  grounding: {sub['grounding'].mean():.2f}  "
                  f"tone: {sub['tone'].mean():.2f}  safety: {sub['safety'].mean():.2f}")

        # human-agreement sample: 20 random judged rows for manual scoring
        sample = judged.sample(min(20, len(judged)), random_state=42)
        sample = sample[["tweet_id", "text", "reply", "grounding", "tone", "safety", "judge_model"]].copy()
        sample["human_grounding"] = ""
        sample["human_tone"] = ""
        sample["human_safety"] = ""
        sample.to_csv("eval/human_agreement_sample.csv", index=False)
        print(f"\nSaved eval/human_agreement_sample.csv -- fill in the human_* "
              f"columns by hand, then run eval/human_agreement.py")

    print(f"\nFull results saved to {args.output}")


if __name__ == "__main__":
    main()