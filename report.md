# Shivika — ComcastCares Support Triage Agent: Report

## 1. Problem Framing

**What "good" means for this agent.** ComcastCares' Twitter support is dominated by
repeat contacts, multi-issue complaints, and public venting. In this environment, a
confidently wrong auto-reply causes more brand damage than a correctly-escalated thread
with no reply at all. Shivika is therefore built to optimize for **calibrated
escalation** — knowing when *not* to act automatically — rather than maximizing
auto-handle rate. This shaped every downstream decision: the intent taxonomy, the
hard-rule escalation logic, and even the metric used to score the system (see §4).

**What we chose not to build.** Shivika is a narrow Tier-1 triage layer, not a
general-purpose ComcastCares chatbot. It does not attempt full resolution, does not try
to sound better than the brand's real voice (replies are grounded in ComcastCares'
actual historical phrasing, not an idealized one), and never has authority over money,
account access, or safety/legal matters — those always reach a human. Full scope
contract in `identity/entity.md`.

## 2. Results vs. Baselines

Evaluated on all 185 labeled examples in the golden set (`eval/golden_set.csv`, 200
total, 15 unlabeled and excluded — see §5).

| System | Intent accuracy | Decision accuracy |
|---|---|---|
| **Shivika** | **75.76%** | **77.27%** |
| Trivial baseline (always most-common) | 28.28% | 77.27% |
| Simple baseline (keyword regex + real hard-rule logic) | 66.16% | 73.74% |

Shivika beats both baselines on intent classification, and roughly matches the simple
baseline on decision accuracy. Average cost-weighted decision score: **0.308** (0 =
perfect; weights taken from the Aim — a wrongly auto-sent escalation-worthy message
costs 5x more than an over-cautious escalation of something safe to auto-send).

That decision-accuracy tie with the simple baseline is itself a red flag worth reading
carefully — see §4.

## 3. Failure Analysis (Top 5, with real examples)

**FM1 — Safety-critical bypass via off_topic/venting misclassification (most severe).**
A message reporting a physical safety incident — *"we love our [Comcast] whole they
allow two 25ft trailers skid down into house filled with children #oops #OSHA
#holeinwall"* — was classified `off_topic` and silently filtered before ever reaching
`decide()`, which is where every hard rule (safety, legal, cancellation, fraud) lives.
**Hypothesis:** `pipeline.py`'s routing treats off_topic/venting as a dead end that
skips hard-rule evaluation entirely — a structural gap, not a classification-accuracy
problem. Any future misclassification into these two buckets silently bypasses every
safety check the system has, regardless of how well those checks work otherwise.

**FM2 — Wrongful auto-send from intent misclassification cascading into decide().**
Six examples (e.g. *"how much would it cost to add FS2 to the channel lineup"* —
billing_dispute misclassified as account_general; *"the record option was removed from
the stream app... nice customer service"* — device_malfunction misclassified as
account_general) were auto-sent because `decide()` trusts the classifier's output
without any independent check against the message content. **Hypothesis:** the
classify() prompt has weak boundaries between account_general and
pricing/feature-complaint phrasing that superficially resembles a simple question.

**FM3 — Wrongful auto-send even with CORRECT classification.** Five examples correctly
classified account_general were still auto-sent when they shouldn't have been (e.g. *"I
want the best internet at the best price... I want just internet"* — a public
price-shopping post, not a safe info request; *"my boyfriend... trying to get
information on a service upgrade... which he never authorized"* — an unauthorized
account-change claim, gold-labeled escalate_priority). **Hypothesis:** the
`NOT_CLEAN_ENOUGH_FOR_AUTO` safety net is a **blocklist** (specific confusion/complaint
keywords), not an **allowlist** (only permitting known-safe question shapes). Blocklists
cannot generalize to phrasings outside their exact keyword set by construction — this
is a structural limitation, not a keyword-coverage gap that more keywords would fully
close.

**FM4 — Adjacent-category confusion under emotional tone.** service_outage,
device_malfunction, and venting boundaries blur when anger and technical symptoms
co-occur (e.g. *"my upload tanking is THEIR problem, NOT MY OWN EQUIPMENT"* —
device_malfunction gold, predicted service_outage). Mostly low-cost since the decision
often still lands correctly, but it inflates the intent-accuracy error count without a
matching real-world cost. **Hypothesis:** the classify() prompt's category definitions
overlap conceptually for messages that report a technical symptom the customer
attributes to the wrong root cause.

**FM5 — Over-escalation on ambiguous severity (safe-direction error).** Several
examples (e.g. repeated *"has a major system issue this morning... wait time from 4-5
minutes to now 7-8 minutes"*) were escalated when gold said draft_hold. This is the
low-cost direction per our own cost matrix (over-caution vs. under-caution), and
arguably a defensible position given the Aim — but worth naming explicitly rather than
treating all decision mismatches as equally bad.

**Data-hygiene note:** the same tweet text appears 3 times in the results (rows 1, 14,
18) under different tweet_ids — a duplication in the golden-set sampling, not caught
before evaluation. Doesn't change the qualitative findings but is worth fixing before
any larger-scale run.

## 4. What's Misleading About My Headline Number

Two things, both quantified rather than hand-waved:

**The judge score is a rubber stamp.** The LLM-judge reported near-perfect quality
scores (grounding 4.99, tone 4.98, safety 5.00 across 172 judged replies) with almost
zero variance. Testing it against 20 independently human-scored examples showed **0%
exact match on tone and safety, and a *negative* correlation on grounding (-0.62)** —
the judge doesn't track human quality judgment at all. We hypothesized an
under-specified rubric, rewrote the prompt with explicit 1-5 calibration anchors and
worked examples, and re-tested on the same 20 rows: **agreement did not improve** (still
0% exact match on all three dimensions). This means every "quality" number this system
reports is currently uninformative — the 75.76%/77.27% headline accuracy numbers are
real (computed against your own hand-labels, not judge output), but reply-quality
claims are not currently backed by working measurement.

**The 5.6% wrongful-auto-send rate is invisible in the headline number.** 77.27%
decision accuracy sounds reasonable in isolation. It does not surface that 11 of 198
evaluated examples (5.6%) were auto-sent when they should have been held for review —
the single costliest error type by design (see cost matrix, §2) — nor that one of those
misclassifications completely bypassed every safety check in the system (FM1). A single
aggregate accuracy number actively obscures both of these, which is exactly why this
section exists.

## 5. What We'd Do With One More Week

1. **Fix the structural safety gap (FM1) first, before anything else.** Route every
   message through hard-rule checking regardless of predicted intent, not just the 5
   "real" intents — off_topic/venting should be able to still trigger escalate_priority
   on a safety/legal keyword hit.
2. **Replace the auto-send blocklist with a positive allowlist.** Instead of "block if
   it contains these bad words," require the message to actively match a small set of
   known-safe question templates (shipping/tracking status, plan feature lookup) before
   allowing auto-send at all.
3. **Rebuild the judge from scratch with a different approach** rather than iterating
   on the same prompt again — likely a larger/different model, or an ensemble of
   several judge prompts checked against each other, since two independent attempts at
   prompt calibration both failed to produce meaningful score variance.
4. **Add few-shot examples to classify() for the billing/account and
   device/outage boundaries** specifically, since FM2 and FM4 both trace back to the
   same handful of confusable phrasing patterns.
5. **De-duplicate the golden set** and expand it past 200 examples, now that the
   sampling/labeling pipeline is proven out — the current size is good for a first pass
   but too small to fully trust the exact percentage points reported here.

See `decision_log.md` for the complete list of engineering decisions and why each was
made, in the order they happened.