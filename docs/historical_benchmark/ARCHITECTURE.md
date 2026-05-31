# AITestArena Historical Benchmark Architecture

Status: project-visible architecture note.
Date: 2026-05-31.

## Goal

Create a separate historical benchmark layer for evaluating betting/prediction sources and AITestArena agents under strict point-in-time rules.

This layer is private/research-only. It is not a live betting system and not a source for live AITestArena ENTER / WAIT / SKIP.

## Core rule

Historical benchmark data is split into two independent layers:

1. `pre_event` — information available before the event.
2. `post_event` — results and evaluation data available only after the event.

Agents or strategies that simulate historical decisions may read only `pre_event` data.

Evaluators may join `pre_event`, historical decisions, and `post_event` after the decision has been created.

## Why this exists

The main risk in historical benchmark work is hindsight leakage. A strategy can look strong if it accidentally sees final score, win margin, closing odds, post-game statistics, or settlement outcome before producing a decision.

The two-layer design prevents that.

## Relationship to live AITestArena

Historical benchmark is separate from the live/paper AITestArena contour.

It must not write to:

- `agent_decisions.csv`
- `candidate_events.csv`
- `odds_snapshots.csv`
- current watchlist
- open positions
- settled positions
- bankroll files
- public watchlist
- current paper-agent cycle

Live AITestArena remains paper-only, with Stalker producing live paper decisions under existing guards.

## Terminology

Live AITestArena decision terms: `ENTER`, `WAIT`, `SKIP`.

Historical benchmark action terms: `PICK`, `PASS`, `NO_DATA`, `VOID`, `BASELINE_PICK`.

Historical benchmark actions are not live AITestArena decisions and must never be written to `agent_decisions.csv`.

## Layers

### Pre-event layer

Contains only event and market information available before the event.

Forbidden: final score, points, win margin, result, settlement, PnL, CLV, post-event statistics, hindsight notes.

### Decision layer

Contains a historical strategy or agent action based only on pre-event input.

It cannot read post-event data.

### Post-event layer

Contains results and settlement fields.

It cannot be agent input.

### Evaluator layer

Joins historical decision and post-event result and computes metrics.

It must not write to live bankroll.

## Current gates completed

- Source discovery.
- Proof-of-data audit.
- Architecture/schema.
- Terminology guard.
- Split sample fixed.

## Next gate

A tiny deterministic historical evaluator over the split sample.

No model, no API, no live files, no bankroll writes.
