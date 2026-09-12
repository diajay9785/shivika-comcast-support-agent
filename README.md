# Shivika — ComcastCares Support Triage Agent

Built for the Hiver SDE Intern take-home assignment.

## What this is
Shivika is a Tier-1 triage agent for ComcastCares on Twitter/X: it classifies each
incoming customer message's intent, drafts a reply grounded in ComcastCares' real
historical resolutions, and decides whether to auto-send or hold for human review —
optimizing for **calibrated escalation, not maximum auto-handle rate** (a confidently
wrong auto-reply costs more than a correctly-escalated one with no reply). See
`identity/entity.md` for Shivika's full scope contract and hard rules, and
`identity/user.md` for who it serves.

## Setup (reproduce in under 15 minutes)
1. `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in your own `GEMINI_API_KEY` (https://aistudio.google.com/apikey)
   and `GROQ_API_KEY` (https://console.groq.com/keys) — both have free tiers
4. Quick demo run (~15-20 customer messages, a couple of minutes):
   ```
   python src/pipeline.py --sample data/shivika_sample.csv --limit 15
   ```
   This prints each message's classified intent, drafted reply (grounded via TF-IDF
   retrieval over 23k+ historical ComcastCares resolutions), and auto-send/hold-for-review
   decision, live.

**Note on free-tier API limits:** both Gemini and Groq's free tiers have real daily/per-minute
caps (documented in `decision_log.md`). The quick demo above stays comfortably within them.
The full golden-set evaluation (below) can take longer and may need a retry if a provider's
quota is hit mid-run — the pipeline is built to checkpoint and resume automatically
(`src/llm_client.py` retries and falls back between providers; `eval/run_eval.py` and
`src/pipeline.py` both skip already-completed rows on re-run).

## Data
- `data/comcast_clean_threads.csv` — full cleaned ComcastCares thread pool (69,983 rows,
  24,021 threads) from the Kaggle "Customer Support on Twitter" dataset, after fixing a
  join-dtype bug and excluding viral mega-thread contamination (see `decision_log.md` #8-9)
- `data/shivika_sample.csv` — fixed, seeded (seed=42) working sample (4,000 rows / 1,381
  threads), sampled by thread so no conversation is cut in half

## Evaluation
`eval/golden_set.csv` — 200 hand-labeled examples (185 individually reviewed and corrected
across 7 stratified buckets, sampled to deliberately oversample ambiguous/multi-issue cases;
see `decision_log.md` for the full sampling and labeling methodology).

To reproduce the full evaluation (185 examples, ~45-60 min depending on API throttling):
```
python eval/run_eval.py
```
Produces `eval/eval_results.csv` (per-row predictions vs. gold labels, cost-weighted
decision scoring, and LLM-judge scores) plus a console summary comparing Shivika against
a trivial baseline (always-most-common) and a simple baseline (keyword regex + real
hard-rule logic).

**Headline results** (185/185 examples): Shivika reached 75.76% intent accuracy / 77.27%
decision accuracy, beating the simple baseline (66.16% / 73.74%) on intent while roughly
matching it on decision accuracy, and beating the trivial baseline (28.28% / 77.27%) on
intent. See `report.md` for what's misleading about these numbers, including a documented
LLM-judge calibration failure found and investigated during evaluation.

`eval/human_agreement_sample.csv` + `eval/human_agreement.py` — the human-vs-judge
agreement check. `eval/rejudge_sample.py` re-scores that same sample with a revised judge
prompt (see `decision_log.md` and `report.md` for why this was needed and what it found).

## Report & decisions
- `report.md` — problem framing, results vs. baselines, failure analysis, what's
  misleading about the headline number, what's next with one more week
- `decision_log.md` — the non-obvious calls made and why, in the order they were made