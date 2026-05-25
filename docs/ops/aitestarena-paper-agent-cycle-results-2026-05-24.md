# AITestArena paper-agent cycle and results analysis — 2026-05-24

## Active source-of-truth status

This document is the compact operational source for NotebookLM / context recovery.

Do not infer operational truth from old wrapper comments, backups, or failed intermediate guard attempts.

## Role boundaries

- Writer is not an AITestArena agent.
- Writer is only for psychology-channel content and FirstMeet AI comments.
- Writer must not touch AITestArena betting, watchlist, bankroll, agent decisions, settlement, cron, server operations, or code.
- Stalker is the AITestArena event scout and paper-only ENTER / WAIT / SKIP candidate writer.
- Sentinel is a read-only OK / WARN / FAIL controller from exported snapshots and compact status files.

## Current paper-agent cycle

The active 07 paper-agent cycle is run by:

`/root/openclaw/workspace/aitestarena/tools/run_aitestarena_hourly_cycle.sh`

The wrapper is intentionally limited to the paper-agent cycle itself:

1. DeepSeek / Stalker safe runner imports or prepares paper decisions.
2. Settlement applies resolved outcomes.
3. Recount normalizes counted void/entry policy state.
4. Results analysis summarizes settled paper performance.
5. Render updates agents, training, watchlist, and public-safe pages.

## Results analysis

Analyzer:

`/root/aitestarena/tools/analyze_agent_paper_results.py`

Outputs:

- `/root/aitestarena/state/agent_paper_results_latest.json`
- `/root/aitestarena/reports/agent_paper_results_*.json`

The analyzer is read-only. It does not edit bankroll, decisions, open positions, settled positions, cron, renderer files, or public HTML.

Parser uses `settlement_outcome` for WIN / LOSS / VOID results.

Latest verified result sample:

- total settled: LOSS 5 / WIN 3
- DeepSeek: LOSS 2 / WIN 1 / pnl rows -62.4
- Silent GPT-5.5: LOSS 2 / WIN 1 / pnl rows -38.5
- Mini Arena Scout: LOSS 1 / WIN 1 / pnl rows -11.2

## Final identity guard — active truth

The active final identity guard is outside the wrapper, in root crontab / cron template:

`ops/cron/root_aitestarena_hourly_cycle_outer_guard.cron`

Active command:

```cron
7 * * * * cd /root/openclaw/workspace/aitestarena && flock -n /tmp/aitestarena_hourly_cycle.lock bash -lc './tools/run_aitestarena_hourly_cycle.sh; rc=$?; /usr/bin/python3 /root/aitestarena/tools/enforce_mini_scout_identity.py >> /root/aitestarena/logs/mini_scout_identity_guard.log 2>&1; exit $rc' >> logs/aitestarena_hourly_cycle.cron.log 2>&1
```

Reason: internal wrapper guards and EXIT traps were tested and were not sufficient. Public-safe/finalize render steps could still leave `/agents/` stale. The working solution is the outer cron guard after full wrapper completion.

## Public agents page invariant

The public `/agents/` page must show:

- Silent GPT-5.5 / GPT-5.5 Thinking / Total bankroll 1000
- Mini Arena Scout / GPT-5.5 / Total bankroll 1000
- DeepSeek / deepseek/deepseek-chat / Total bankroll 1000

Settled histories must remain visible as:

`История paper-ставок / Settled paper history`

History data also exists in:

- `/var/www/aitestarena/data/agents/<agent_id>/history.json`
- `/root/aitestarena/agents/<agent_id>/positions_settled.jsonl`

## What NotebookLM must not conclude

- Do not say the active final guard is an EXIT trap.
- Do not say Writer is an AITestArena betting/watchlist role.
- Do not say analysis changes bankroll.
- Do not say real-money betting is involved.
- Do not treat old backups or failed intermediate guard attempts as active truth.

## Safe check after any change

Run or inspect:

1. `bash -n /root/openclaw/workspace/aitestarena/tools/run_aitestarena_hourly_cycle.sh`
2. one manual exact cron-command run if needed;
3. check `RESULTS_ANALYSIS_OK`, `results_analysis_rc=0`, `CYCLE_DONE status=OK`;
4. curl `/agents/` and verify names/models/bankroll 1000 and visible settled histories.
