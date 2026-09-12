# Decision Log

1. **Brand: ComcastCares.** Chosen over airline/other-telecom options for its clear,
   data-supported escalation pattern (public thread → DM/phone handoff) and
   self-contained resolutions, which makes reply-grounding tractable.

2. **Aim: optimize for calibrated escalation, not max auto-handle rate.** ComcastCares
   threads are noisy (repeat contacts, multi-issue complaints, venting); a confidently
   wrong auto-reply costs more than a correct escalation with no reply.

3. **One agent (Shivika), three sequential functions** (classify → draft → decide),
   not three separate agents and not a fourth "forward" step — escalating IS the
   forward, and no real routing infrastructure exists to route into.

4. **Classify, draft, and decide kept as three separate LLM calls**, not combined,
   to preserve clean failure attribution for the failure-analysis section.

5. **LLM stack: Gemini (free tier) primary, Groq (free tier) fallback** on rate-limit
   errors only — a real constraint from having no paid API access, documented rather
   than hidden. Judge results are tagged by `judge_model` and reported separately per
   model, never pooled, in case the fallback affects agreement scores.

6. **Retrieval: TF-IDF/keyword search**, not embeddings — free, fast, and fully
   explainable (can point to the exact matched historical thread by term overlap).

7. **Framework: plain Python, no LangChain** — fewer abstraction layers to defend
   live, and unnecessary at this pipeline's size.

8. **Data-quality fix #1: dtype bug in initial filter.** `tweet_id`/`in_response_to_tweet_id`
   cast to str(float) produced mismatched IDs (e.g. "123.0" vs "123"), silently dropping
   every customer-side message. Fixed by casting to nullable Int64 before joining.

9. **Data-quality fix #2: viral mega-thread contamination.** Connected-components
   thread reconstruction merged hundreds of unrelated customers who replied to the same
   viral corporate tweet into one fake "conversation." Excluded threads >20 rows
   (~4.2% of rows) as non-support noise.

10. **Sample: fixed, seeded (seed=42) 4,000-row / 1,381-thread sample**, drawn by
    thread (not raw row) so no conversation is cut in half.

11. **Intent taxonomy: 5 real intents + 2 non-support routing categories**, derived
    from the data (not Banking77): Service Outage/Connectivity, Billing/Charge Dispute,
    Equipment/Device Malfunction, Installation/Appointment Scheduling, Account/General
    Inquiry; plus Venting/Non-Actionable (acknowledge-and-hold-low-priority, not drafted
    normally) and Off-Topic/Not a Support Request (filtered before classification).

12. **Golden set: 200 examples, stratified + deliberately oversampled for ambiguity.**
    30 examples chosen specifically for multi-issue/ambiguous signal (per the Aim),
    remainder stratified across the 5 real intents + venting, plus a held-out
    "unmatched" pool sampled blind rather than assumed off-topic.

13. **Golden-set threads excluded from the retrieval corpus** used at evaluation time,
    to prevent the reply-grounding step from retrieving its own answer (data leakage).

14. **Labeling process: LLM-proposed, human-corrected.** Labels initially proposed
    (by Claude, during the build session — distinct from the Gemini/Groq production
    pipeline) then reviewed and corrected by hand. Disclosed openly per Hiver's rule
    that AI-assisted work must be explainable, not hidden.

15. **Hard rules generalized from literal keywords to three named semantic
    categories.** Originally: explicit cancellation keywords only. During golden-set
    labeling, the same gap-class surfaced three separate times independently —
    an unauthorized-billing claim ("never been a customer, but got billed $300"),
    a competitor-switch threat ("time to find a new provider"), and explicit
    cancellation language — none of which are caught by a fixed keyword list if
    phrased plainly. Generalized to three named, bounded categories (not an
    open-ended semantic classifier): (1) explicit cancellation language,
    (2) unauthorized-billing/no-customer-relationship claims, (3) competitor-switch/
    churn threats. All three route to escalate_priority for the same reason: a wrong
    auto-response on any of them has outsized cost (lost customer, legal exposure,
    reputational damage), directly tied to the Aim.

16. **Deliberate inconsistency, stated plainly:** "fraud"/"scam" were kept as plain
    literal keywords rather than given the same semantic-pattern treatment as #15.
    This is an accepted time-tradeoff, not an overlooked gap — escalate_priority and
    draft_hold both route to a human either way, so a loose match on "fraud"/"scam"
    only affects queue priority, not auto-send risk, making the lower rigor cheap
    to accept here specifically.

17. **Auto-send narrowed further after eval revealed a real gap.** The first eval
    run (15 examples) showed AUTO_SEND_INTENTS = {account_general} was too blunt --
    it wrongly auto-sent a confused signup-email question and, worse, a misclassified
    billing dispute (the exact costly-error pattern the Aim exists to prevent). Across
    all 200 golden-set examples, only one was ever confirmed genuinely safe to
    auto-send (a clean, simple "will the modem ship or do I pick it up" question).
    Added a NOT_CLEAN_ENOUGH_FOR_AUTO keyword check: account_general messages
    containing confusion/complaint signals fall back to draft_hold even though the
    intent matches. Also strengthened classify.py's prompt with an explicit rule and
    examples for the venting-vs-real-issue distinction, after the same eval run showed
    two real device/outage complaints misclassified as venting -- the prompt had never
    been given the "no actionable request underneath" principle established during
    golden-set labeling, it was just a bare category list.