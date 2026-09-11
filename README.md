# Shivika — ComcastCares Support Triage Agent

Built for the Hiver SDE Intern take-home assignment.

## What this is
Shivika triages incoming ComcastCares tweets: classifies intent, drafts a reply grounded
in ComcastCares' historical resolutions, and decides whether to auto-send or escalate to
a human — see `identity/entity.md` for the full scope contract and `identity/user.md`
for who it serves.

## Setup (reproduce in under 15 minutes)
1. `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in your own `GEMINI_API_KEY` / `GROQ_API_KEY`
4. `python src/pipeline.py --sample data/shivika_sample.csv`

## Data
- `data/comcast_clean_threads.csv` — full cleaned ComcastCares thread pool (69,983 rows,
  24,021 threads), after excluding viral mega-thread contamination (see decision_log.md)
- `data/shivika_sample.csv` — fixed, seeded working sample (4,000 rows / 1,381 threads)

## Evaluation
See `eval/` for the golden set, LLM-as-judge, and baselines. Run `python eval/run_eval.py`.

## Report & decisions
- `report.md` — problem framing, results vs. baselines, failure analysis, what's next
- `decision_log.md` — the non-obvious calls made and why
