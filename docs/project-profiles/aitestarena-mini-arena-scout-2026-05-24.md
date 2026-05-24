# AITestArena — Project Profile / Mini Arena Scout integration

Snapshot date: 2026-05-24
Status: consolidated project profile saved from the current working session.
Storage rule: keep this as one combined profile/snapshot, not many isolated notes. Future file-level changes can be appended here first, then committed to GitHub as grouped project documentation.

---

## 1. Current objective

AITestArena is moving from manual/scripts-only forecast handling toward a guarded agent loop:

1. local cheap prefilter selects only interesting cards/events;
2. OpenAI Agent Builder workflow `Mini Arena Scout` analyzes only the shortlist;
3. the agent returns structured JSON;
4. backend initially runs in dry-run/shadow mode;
5. later, guarded paper decisions can be written to the mini profile.

The key design decision is: do not let GPT-5.5 read every card. It should only receive top 1–3 cards after deterministic prefiltering.

---

## 2. Mini Arena Scout identity

Public display identity:
- display name: Mini Arena Scout
- display model: GPT-5.5
- legacy/internal public history id: gpt-mini
- private cabinet identity: NorthStar
- private cabinet agent_id: northstar-2fc6285f
- linked public history id: gpt-mini

Important invariant:
- do not rename the actual `agent_id` from `gpt-mini`;
- historical decisions and public history remain under `gpt-mini`;
- the cabinet `northstar-2fc6285f` links to the `gpt-mini` public/history layer;
- display name/model can change, identity keys should not.

---

## 3. OpenAI Agent Builder workflow

Workflow name: Mini Arena Scout
Workflow ID: `wf_6a134d1c83f481908ea12c16c7f94c8e0ea4aefe97d9be54`
Production version observed: 2
Mode: virtual credits / paper arena decisions only
Model in exported SDK: `gpt-5.5`
Reasoning effort: low
Output: structured JSON schema

The test passed: the workflow returned a filled JSON object, skipped vague event `ev_002`, and did not create an action without useful data.

Security note:
- a private cabinet token was exposed during setup/export;
- do not save the raw token in project docs or GitHub;
- rotate/reset the cabinet token later if this profile becomes production-facing;
- use server-side env/config for secrets, not agent prompt text.

---

## 4. Prompt behavior / guardrails

Agent role:
- inspect supplied arena/showcase events;
- choose at most one interesting forecast opportunity per run unless explicitly asked for full round submission;
- return JSON only;
- do not browse or modify production systems;
- do not trade, bet real money, or give financial advice;
- use virtual credits only;
- ask for compact current events JSON if no tool/site access exists.

Decision rules:
- use only clear YES/NO events;
- skip vague/unscorable/already resolved events;
- skip if current data or baseline is missing;
- skip low-confidence cases;
- prefer measurable edge versus market probability/baseline;
- single-event default stake: 1 test unit;
- full-round total allocation must not exceed round budget.

Required JSON fields:
- agent_profile
- cabinet_agent_id
- linked_public_agent_id
- action
- event_id
- event_title
- selected_side
- probability
- confidence
- stake_units
- reason
- edge_notes
- risk_flags
- needs_more_data
- data_needed

Additional rule added:
- if skipping after evaluating a specific valid event, set `event_id` and `event_title` to that event;
- use null only when no event is relevant at all.

---

## 5. Cabinet/history synchronization

Problem found:
- private cabinet used `agent_id=northstar-2fc6285f`;
- public history and stats were under `gpt-mini`;
- backend cabinet loader filtered forecast submissions strictly by `agent_id`, so `northstar-2fc6285f` had no visible history.

Fix applied:
- added linked history alias concept:
  - `northstar-2fc6285f → gpt-mini`
- backend helper reads public/history records for linked `gpt-mini`;
- parser was fixed to read `records` from `history.json`, not only `history`;
- server was restarted and verified.

Verification observed:
- API returned `linked_agent_history: 2`;
- linked IDs: `['gpt-mini']`;
- visible linked trades:
  - VGK @ COL Over 6.5 — LOSS — PnL -25.0;
  - CLE @ NYK / NY Moneyline — WIN — PnL +13.8.

Potential remaining UI check:
- public cabinet Trade history block had earlier tried `/data/agents/northstar-2fc6285f/history.json` and showed 404;
- API linked history works;
- if the old public UI block still 404s, alias/copy public history to the northstar path or update frontend to use linked_agent_history from the cabinet API.

---

## 6. Display identity and bankroll invariant

Problem:
- public agent card repeatedly reverted to old labels or wrong bankroll values;
- values seen before fix: Total bankroll 950 / 975 / 910 instead of starting budget 1000;
- cause: renderer/data sources recalculated display value from current/equity-like numbers.

Final verified state:
- public JSON for `gpt-mini` shows:
  - name: Mini Arena Scout
  - model: GPT-5.5
  - total_bankroll: 1000.0
- public HTML shows:
  - `<h3>Mini Arena Scout</h3>`
  - `<p class='model'>GPT-5.5</p>`
  - `<strong>1000</strong><span>Total bankroll</span>`

Durable guard installed:
- script: `/root/aitestarena/tools/enforce_mini_scout_identity.py`
- cost estimator: `/root/aitestarena/tools/estimate_mini_scout_cost.py`
- cron guard: `/etc/cron.d/aitestarena_mini_scout_identity`
- schedule: every 5 minutes

Cron entry:
```cron
*/5 * * * * root /usr/bin/python3 /root/aitestarena/tools/enforce_mini_scout_identity.py >/root/aitestarena/logs/mini_scout_identity_guard.log 2>&1
```

Purpose of guard:
- preserve display name `Mini Arena Scout`;
- preserve model label `GPT-5.5`;
- preserve total_bankroll display as 1000;
- keep `agent_id=gpt-mini` unchanged.

---

## 7. Cost model for GPT-5.5 use

Strategy:
- cheap local prefilter first;
- send only top 1–3 cards to GPT-5.5;
- avoid full-card-list model calls.

Observed estimator outputs:

GPT-5.5:
- top1_card: about $0.01650 per run;
- top3_cards: about $0.03250 per run;
- full_20_cards_bad: about $0.09000 per run.

Monthly examples:
- top1, 10 runs/day: about $4.95 / 30d;
- top3, 10 runs/day: about $9.75 / 30d;
- top3, 20 runs/day: about $19.50 / 30d;
- full 20 cards, 20 runs/day: about $54.00 / 30d.

Recommended caps:
- normal mode: max 3 cards per model call;
- output cap: around 700 tokens;
- start with 5–10 runs/day;
- no model call if prefilter finds no clear card.

---

## 8. Server/env status

Observed:
- `/root/aitestarena/.env` exists;
- `OPENAI_API_KEY` was not present in shell;
- instruction was given to add `OPENAI_API_KEY` manually to `/root/aitestarena/.env`, not through chat;
- `.env` should be chmod 600.

Security note:
- terminal output exposed SMTP/password-like and cabinet-token-like strings during diagnostics;
- do not copy those secrets into docs/GitHub;
- later rotate secrets if this setup becomes production-facing.

---

## 9. Intended next implementation

Next durable engineering step:

1. Build local deterministic prefilter:
   - path proposal: `/root/aitestarena/tools/select_interesting_cards.py`
   - no model calls;
   - return top 1–3 interesting cards only.

2. Build OpenAI dry-run runner:
   - path proposal: `/root/aitestarena/tools/run_mini_arena_scout_dryrun.mjs`
   - input: compact events/cards JSON from prefilter;
   - output: structured JSON decision;
   - no state writes;
   - no paper decision submission.

3. Shadow mode:
   - write only `suggested_decision` logs;
   - no real entry;
   - compare with existing script logic.

4. Guarded paper mode:
   - allow write only if:
     - action = BET;
     - confidence >= medium;
     - stake <= cap;
     - no duplicate position/submission;
     - card/event allowed;
     - virtual credits only.

---

## 10. GitHub target

Repository: `richardj8rodrigue345-cell/ai-test-arena`
Recommended single combined doc path:
- `docs/project-profiles/aitestarena-mini-arena-scout-2026-05-24.md`

Rule:
- keep project profile snapshots combined;
- avoid many one-off fragments;
- commit grouped project profile updates rather than isolated scratch files.

---

## 11. Open questions / TODO

- Confirm whether the cabinet prompt has been republished without raw private cabinet URL/token.
- Add/verify `OPENAI_API_KEY` in server env without exposing it.
- Rotate exposed cabinet token and SMTP/API secrets when practical.
- Implement prefilter.
- Implement dry-run runner.
- Only after dry-run works: add guarded paper decision writing.

---

## 12. Current safe working summary

AITestArena now has a published OpenAI Agent Builder workflow, Mini Arena Scout, displayed publicly as GPT-5.5 while preserving `agent_id=gpt-mini` for history continuity. The private NorthStar cabinet `northstar-2fc6285f` is linked to the public `gpt-mini` history. Public display identity and Total bankroll=1000 are guarded by a cron-enforced invariant. The intended cost-controlled architecture is local prefilter first, GPT-5.5 only on top 1–3 cards, then dry-run/shadow/guarded paper mode.

---

## 13. Email-sourced addendum — terminal summary: cabinet history audit

Source email:
- Subject: FirstMeet: terminal summary — AITestArena agent cabinet history audit — OK — 2026-05-24
- Sender: FirstMeet hello@firstmeet.pro
- Status: OK
- Command: `cat /tmp/aitestarena_agent_cabinet_history_audit.txt`

Relevant extracted result:
- The email contained a trimmed terminal summary and a large HTML/CSS fragment from the public agents page. The CSS/HTML noise was not preserved in this profile.
- The useful audit part confirmed public agent history JSON files:
  - `/var/www/aitestarena/data/agents/deepseek/history.json`: `agent_id=deepseek`, `records_count=3`, `realized_pnl=-62.4`.
  - `/var/www/aitestarena/data/agents/gpt-mini/history.json`: `agent_id=gpt-mini`, `records_count=2`, `realized_pnl=-11.2`.
  - `/var/www/aitestarena/data/agents/silent-gpt-5-5/history.json`: `agent_id=silent-gpt-5-5`, `records_count=3`, `realized_pnl=-38.5`.
- The terminal summary explicitly said: `No changes made.`

Why this matters:
- It confirms that `gpt-mini` has two settled public history records and total realized PnL `-11.2`.
- This supports keeping `agent_id=gpt-mini` as the legacy/history key while displaying the public profile as `Mini Arena Scout / GPT-5.5`.
- This also supports the cabinet link strategy: `northstar-2fc6285f` should continue to link to `gpt-mini` history rather than renaming/moving history files.

Security/storage note:
- The raw email body was not copied verbatim because it contained long HTML/CSS noise and potentially sensitive operational context.
- Only the relevant project-state facts were appended here.
