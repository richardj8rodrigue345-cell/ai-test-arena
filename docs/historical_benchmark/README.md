# AITestArena Historical Benchmark

Status: project-visible docs and training material for the separate historical benchmark direction.

This directory is not part of the live AITestArena paper-agent cycle.

## Purpose

Evaluate historical betting/prediction sources and strategies under strict point-in-time rules.

The first vertical is NBA historical benchmark.

## Safety invariant

Historical benchmark must never contaminate live AITestArena decisions.

Do not write historical benchmark data to:

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

## Required split

- `pre_event`: information available before the event. No result fields.
- `post_event`: result and settlement fields. Evaluator-only, not agent input.
- `decisions`: historical strategy actions only, not live ENTER/WAIT/SKIP.
- `evaluator`: deterministic metrics only, no live bankroll writes.

## Files

- `ARCHITECTURE.md`
- `SCHEMA_PRE_EVENT.md`
- `SCHEMA_POST_EVENT.md`
- `SCHEMA_DECISIONS.md`
- `SCHEMA_EVALUATOR.md`
- `samples/`

## Next gate

Gate 3: tiny deterministic evaluator over a 20-row split sample.

Rules:

- no model calls;
- no API calls;
- no live files;
- no live bankroll writes;
- no production changes.
