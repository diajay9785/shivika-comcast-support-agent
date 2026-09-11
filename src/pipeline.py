import argparse
import os
import pandas as pd

from retrieval import build_corpus, retrieve_examples
from classify import classify
from draft import draft_reply
from decide import decide


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    parser.add_argument("--corpus", default="data/comcast_clean_threads.csv")
    parser.add_argument("--limit", type=int, default=None,
                         help="Only process the first N customer messages (for testing)")
    parser.add_argument("--output", default="data/pipeline_results.csv",
                         help="Where results are saved incrementally")
    args = parser.parse_args()

    n_pairs = build_corpus(args.corpus)
    print(f"Retrieval corpus built: {n_pairs} historical reply pairs\n")

    df = pd.read_csv(args.sample)
    df = df[df["inbound"] == True]
    if args.limit:
        df = df.head(args.limit)

    # resume support: skip rows already processed in a previous run
    done_ids = set()
    if os.path.exists(args.output):
        done_ids = set(pd.read_csv(args.output)["tweet_id"].astype(str))
        print(f"Resuming -- {len(done_ids)} rows already done, skipping those.\n")

    results = []
    for i, (_, row) in enumerate(df.iterrows()):
        if str(row["tweet_id"]) in done_ids:
            continue

        text = row["text"]
        intent, classify_model = classify(text)

        if intent == "off_topic":
            # filtered before drafting entirely -- not a support request
            record = {
                "tweet_id": row["tweet_id"], "text": text, "intent": intent,
                "reply": None, "decision": "filtered_off_topic",
                "classify_model": classify_model, "draft_model": None,
            }
        elif intent == "venting":
            # acknowledged, held low priority -- not run through normal
            # grounded drafting (see identity/entity.md)
            record = {
                "tweet_id": row["tweet_id"], "text": text, "intent": intent,
                "reply": "[acknowledge-and-hold-low-priority -- no drafted reply]",
                "decision": "hold_low_priority",
                "classify_model": classify_model, "draft_model": None,
            }
        else:
            examples = retrieve_examples(text, n=3)
            reply, draft_model = draft_reply(text, examples)
            decision = decide(intent, text)
            record = {
                "tweet_id": row["tweet_id"], "text": text, "intent": intent,
                "reply": reply, "decision": decision,
                "classify_model": classify_model, "draft_model": draft_model,
            }

        results.append(record)
        print(f"\n[{i+1}] Customer:", text[:100])
        print("Intent:", record["intent"], "| Decision:", record["decision"])

        # checkpoint every row -- a dropped connection never loses more
        # than the single row in flight
        pd.DataFrame(results).to_csv(
            args.output, mode="a", header=not os.path.exists(args.output), index=False
        )
        results = []

    print(f"\nDone. Results saved to {args.output}")


if __name__ == "__main__":
    main()