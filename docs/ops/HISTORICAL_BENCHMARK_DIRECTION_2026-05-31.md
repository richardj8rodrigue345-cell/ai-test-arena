# AITestArena Historical Benchmark Direction — 2026-05-31

Status: active project direction / private research benchmark layer.

## Purpose

AITestArena is adding a separate Historical Benchmark Lab for evaluating historical sports betting / prediction sources and AI-agent strategies.

This is not a live betting system and not a real-money workflow.

The goal is to test whether historical prediction sources, external model repos, and AITestArena internal agents can be compared fairly under strict point-in-time rules.

## Current decision

The project direction is to focus on historical sports betting benchmark rather than crypto/presale research.

The first practical vertical is NBA historical benchmark using:

- kyleskom/NBA-Machine-Learning-Sports-Betting as historical NBA odds/results baseline dataset;
- NBA-Betting/NBA_AI as a model/prediction pipeline candidate after leakage audit;
- The Odds API historical only as a future CLV evaluator, not as a prediction source.

## Critical invariant: two-layer history

Historical data must be separated into:

1. Pre-event layer
   - Contains only data available before the event.
   - Must not contain results, final score, win margin, PnL, settlement, CLV, or hindsight fields.
   - May be used for historical simulation / decision replay only.

2. Post-event / evaluator layer
   - Contains result, settlement, PnL, CLV, and evaluation metrics.
   - Must not become agent input.
   - Used only after a historical decision/action has been produced.

## Terminology guard

Live AITestArena uses ENTER / WAIT / SKIP in `agent_decisions.csv`.

Historical benchmark must not use live ENTER / WAIT / SKIP as historical decision commands.

Historical benchmark actions are separate, such as `PICK`, `PASS`, `NO_DATA`, `VOID`, or `BASELINE_PICK`.

Historical benchmark files must never be written to:

- `agent_decisions.csv`
- `candidate_events.csv`
- `odds_snapshots.csv`
- current watchlist
- open positions
- settled positions
- bankroll files
- live Stalker outbox
- public watchlist
- current paper-agent cycle

## Completed gates on 2026-05-31

- Source discovery: complete.
- Proof-of-data audit: complete.
- Architecture/schema docs: complete.
- Terminology guard: complete.
- Split sample: fixed and passed safety checks.

## Current validated sample

The kyleskom split sample was validated in the server workspace under `historical_benchmark/samples/` and copied into GitHub docs as public/project-visible training material.

The sample separates:

- `pre_event_sample_kyleskom_2026-05-31.jsonl`
- `post_event_sample_kyleskom_2026-05-31.jsonl`

Safety checks passed on the server:

- pre_count = post_count = 20
- event_ids_match = true
- no forbidden result fields in pre_event
- pre_event result_known = false
- all rows not_for_live_decision_use = true
- post_event not_for_agent_input = true

## What this does not change

This direction does not change:

- live Stalker ENTER / WAIT / SKIP rules;
- The Odds API live scanning;
- bankroll;
- positions;
- settlement;
- cron;
- nginx;
- public pages;
- current watchlist;
- `agent_decisions.csv`;
- `candidate_events.csv`;
- `odds_snapshots.csv`.

## Next gate

Gate 3 should be a tiny deterministic historical evaluator over the split sample.

Evaluator requirements:

- no model call;
- no API call;
- no live files;
- no live bankroll writes;
- no production changes;
- reads only historical benchmark sample files;
- writes only historical benchmark evaluator sample files.

## Safety phrase

Historical benchmark data is for private/research evaluation only: no live decision mixing, no betting actions, no production changes.
