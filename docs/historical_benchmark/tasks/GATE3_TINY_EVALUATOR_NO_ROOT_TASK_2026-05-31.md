# Gate 3 — Tiny Historical Evaluator Task (No Root)

Date: 2026-05-31.

Status: next bounded task for AITestArena Historical Benchmark Lab.

## Context

AITestArena agents do not have root access.

This task must use relative workspace paths only.

This is not a live AITestArena decision pass and not a betting workflow.

## Hard boundaries

Do not read or write:

- `/root/...`
- `/var/www/...`
- cron
- nginx
- systemd
- production files
- `agent_decisions.csv`
- `candidate_events.csv`
- `odds_snapshots.csv`
- bankroll files
- positions files
- settlement files
- current watchlist
- public watchlist
- live Stalker outbox
- public pages

Do not call:

- models
- external APIs
- The Odds API
- email tools
- real betting accounts

## Allowed workspace paths

Input files, relative to workspace:

- `historical_benchmark/samples/pre_event_sample_kyleskom_2026-05-31.jsonl`
- `historical_benchmark/samples/post_event_sample_kyleskom_2026-05-31.jsonl`

Output files, relative to workspace:

- `historical_benchmark/runs/historical_decisions_sample_2026-05-31.jsonl`
- `historical_benchmark/runs/evaluator_metrics_sample_2026-05-31.jsonl`
- `historical_benchmark/runs/run_2026-05-31_tiny_evaluator.md`

Create `historical_benchmark/runs/` if it does not exist.

## Objective

Create a deterministic tiny evaluator over the existing split sample.

The evaluator must prove the training/replay loop shape:

`pre_event -> historical decisions -> post_event -> evaluator metrics`

## Decision layer

Create baseline historical decisions from pre-event only.

Strategies:

1. `baseline_home_moneyline`
   - `historical_action=BASELINE_PICK`
   - selection `home`
   - stake `1.0`

2. `baseline_away_moneyline`
   - selection `away`
   - use only if away odds are available in the sample;
   - otherwise write `NO_DATA`, do not invent odds.

3. `baseline_favorite_moneyline`
   - choose the lower decimal odds if both home and away odds are available;
   - otherwise write `NO_DATA`.

4. `baseline_underdog_moneyline`
   - choose the higher decimal odds if both home and away odds are available;
   - otherwise write `NO_DATA`.

## Historical decision row schema

Each row should include:

```json
{
  "decision_id": "...",
  "event_id": "...",
  "source_strategy": "...",
  "historical_action": "BASELINE_PICK | PASS | NO_DATA",
  "market": "moneyline",
  "selection": "home | away | null",
  "odds_at_decision": 0.0,
  "stake_units": 1.0,
  "input_layer": "pre_event_only",
  "not_for_live_decision_use": true,
  "does_not_write_to_agent_decisions_csv": true
}
```

## Evaluator rules

The evaluator may read post-event only after historical decisions have been created.

For home selection, use `result_home_moneyline`.

For away selection, use `result_away_moneyline`.

PnL:

- WIN: `stake_units * (odds_at_decision - 1)`
- LOSS: `-stake_units`
- PUSH/VOID/PASS/NO_DATA: `0`

## Evaluator row schema

Each row should include:

```json
{
  "evaluation_id": "...",
  "decision_id": "...",
  "event_id": "...",
  "source_strategy": "...",
  "historical_action": "...",
  "result": "WIN | LOSS | PUSH | VOID | NO_DATA",
  "stake_units": 1.0,
  "odds_at_decision": 0.0,
  "pnl_units": 0.0,
  "roi": 0.0,
  "not_for_agent_input": true,
  "not_for_live_decision_use": true,
  "does_not_write_to_live_bankroll": true
}
```

## Markdown report requirements

`historical_benchmark/runs/run_2026-05-31_tiny_evaluator.md` must include:

1. Title: `Historical Tiny Evaluator Run — 2026-05-31`.
2. Input files.
3. Safety confirmation:
   - pre-event only used for decisions;
   - post-event only used by evaluator;
   - no live files read;
   - no live files written;
   - no model/API calls;
   - no root paths used.
4. Row counts:
   - pre-event rows;
   - post-event rows;
   - historical decision rows;
   - evaluator rows.
5. Strategy summary table:
   - strategy;
   - picks;
   - no_data/pass;
   - wins;
   - losses;
   - pushes/voids;
   - pnl_units;
   - roi.
6. Limitations:
   - timestamp quality is weak;
   - game date only, no exact pick timestamp;
   - no CLV yet;
   - away/favorite/underdog baselines are limited if away odds are absent.
7. Safety footer:
   - `Tiny evaluator complete: historical benchmark only, no live decision mixing, no betting actions, no production changes.`

## Quality checks

Required checks:

- pre-event event_ids equal post-event event_ids;
- no forbidden result fields in pre-event;
- all decisions have `not_for_live_decision_use=true`;
- all decisions have `does_not_write_to_agent_decisions_csv=true`;
- all evaluator rows have `does_not_write_to_live_bankroll=true`;
- all output files are under `historical_benchmark/runs/`.

## Expected final chat response

If successful, reply only:

`DONE tiny evaluator saved to historical_benchmark/runs/. No live decision mixing, no betting actions, no production changes.`

If failed, reply only:

`FAILED tiny evaluator: <short reason>. No live decision mixing, no betting actions, no production changes.`
