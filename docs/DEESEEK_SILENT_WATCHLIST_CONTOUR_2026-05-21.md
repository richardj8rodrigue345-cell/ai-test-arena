# AITestArena — DeepSeek + Silent/GPT55-policy watchlist contour

Date: 2026-05-21
Status: active design note
Scope: AITestArena watchlist, paper benchmark, virtual credits only

## Purpose

This document records the linked hourly decision contour for AITestArena.

The contour connects:

- DeepSeek direct API paper-agent;
- Silent/GPT55-policy server-side decision script;
- watchlist/outbox CSV files;
- guard and normalization layer;
- official import/render scripts;
- future settlement, results, and dynamic policy logic.

This is not real betting, not trading, and not account automation. It is a paper benchmark using virtual credits only.

## Current linked flow

```text
root cron, minute 7 hourly
→ /root/openclaw/workspace/aitestarena/tools/run_deepseek_watchlist_safe.sh --apply
→ direct_deepseek_runner.py
→ DeepSeek API direct decision pass
→ /root/aitestarena/tools/silent_gpt55_auto_decide.py
→ tools/import_silent_gpt55_actions_to_decisions.py
→ aitestarena_watchlist_outbox/agent_decisions.csv
→ normalize statuses to ENTER / WAIT / SKIP
→ /root/aitestarena/tools/import_agent_decisions_outbox.py
→ /root/aitestarena/tools/render_agents_leaderboard.py
→ /root/aitestarena/tools/process_watchlist_outbox.py
→ watchlist, agent table, training/history pages updated
```

## Cron

Current root crontab entry:

```cron
7 * * * * cd /root/openclaw/workspace/aitestarena && flock -n /tmp/aitestarena_deepseek_direct_safe.lock ./tools/run_deepseek_watchlist_safe.sh --apply >> logs/deepseek_direct_safe.cron.log 2>&1
```

Meaning:

- runs once per hour on minute 7;
- enters the correct workspace;
- uses `flock` to prevent overlapping runs;
- calls the safe wrapper, not the raw runner;
- writes cron-level logs to `logs/deepseek_direct_safe.cron.log`.

## Agents

```text
deepseek
silent-gpt55-policy
```

DeepSeek is the direct API scout/decision agent.

Silent/GPT55-policy is not the live ChatGPT app model. It is the server-side policy script that encodes the GPT-5.5/Silent decision logic written earlier. This keeps the app subscription/billing separate from server automation and avoids trying to wake the ChatGPT app directly.

## DeepSeek direct runner

Path:

```text
direct_deepseek_runner.py
```

Current function:

1. read `candidate_events.csv`;
2. read `odds_snapshots.csv`;
3. select active candidates;
4. build a compact odds/context prompt;
5. call DeepSeek Chat API directly;
6. parse model response;
7. apply guard logic;
8. append raw decisions/statuses to `aitestarena_watchlist_outbox/agent_decisions.csv`.

DeepSeek API key location on server:

```text
/root/openclaw/workspace/aitestarena/secrets/deepseek.env
```

The key must never be printed into chat, committed to GitHub, or stored in Google Drive.

## Guard policy

The contour is paper-only. It must not log in to accounts, click betting buttons, place real bets, or use real money.

Guard blocks or avoids `ENTER` unless all of the following are true:

- at least two independent sources confirm the same market;
- a fair probability exists;
- EV is positive;
- Kelly is positive;
- event has not started and deadline has not expired;
- market line is valid and directly comparable;
- allocation respects risk limits.

If the market is single-source only, the action should be `WAIT` or a service status such as `NEEDS_SECOND_SOURCE`, later normalized.

If the event started before confirmation, it should become `SKIP` with reason `EXPIRED_SECOND_SOURCE`.

If EV is not positive, it should become `SKIP` with reason `NO_VALUE`.

## Silent/GPT55-policy bridge

Silent writes actions into:

```text
/root/aitestarena/logs/silent_gpt55_auto_decide.log
```

The bridge reads only new lines after its watermark and converts real actions into agent decisions:

```text
tools/import_silent_gpt55_actions_to_decisions.py
```

It ignores `skipped_duplicate_observation`, so old duplicate WAIT/SKIP observations do not pollute trading history.

When Silent produces a new real action, it becomes a separate row:

```csv
silent-gpt55-policy,<event_id>,ENTER,25,"silent_gpt55_policy: ENTER; imported from silent_auto_actions",<timestamp>
```

## Agent registry

`silent-gpt55-policy` is registered in:

```text
/root/aitestarena/agents/registry.json
```

It was verified with:

```bash
python3 /root/aitestarena/tools/record_agent_decision.py --dry-run
```

using a valid watchlist event id. The recorder accepted the agent as active.

## Decision vocabulary

The official recorder accepts only:

```text
ENTER
WAIT
SKIP
```

Analytical statuses remain in the `reason` field and are normalized before import.

Mapping:

```text
NEEDS_SECOND_SOURCE   → WAIT
EXPIRED_SECOND_SOURCE → SKIP
NO_VALUE              → SKIP
NO_ENTRY              → SKIP
CONFIRMED_LINE        → WAIT
MODEL_CHECKED         → WAIT
```

This preserves useful analytic meaning without breaking `record_agent_decision.py`.

## Why this matters

The system should not treat a model’s reasoning as a real trading system until the full loop exists:

1. populate watchlist / showcase;
2. collect odds and source evidence;
3. run DeepSeek and Silent/GPT55-policy decision passes;
4. allow `ENTER` only when guard conditions are satisfied;
5. record paper-only virtual-credit positions;
6. resolve outcomes after games/events;
7. calculate PnL, accuracy, Brier, CLV, and discipline metrics;
8. update trading history and agent leaderboard;
9. adapt future agent behavior from measured results, not from one-off guesses.

## Next implementation phase — result counting and dynamic changes

Required next subsystem:

```text
settlement_worker
→ read open paper positions and watchlist events
→ fetch/verify official result source
→ mark WIN / LOSS / VOID / EXPIRED_SECOND_SOURCE / NO_ENTRY
→ compute virtual PnL and bankroll change
→ append trading history
→ update agent metrics
→ render leaderboard and history
→ feed aggregate performance back into future allocation and decision thresholds
```

Required metrics:

- Paper PnL by agent and event;
- bankroll over time;
- win/loss/void count;
- Brier score for probability calibration;
- accuracy for directional outcomes;
- closing line value when closing odds are available;
- discipline metrics: skipped no-value, skipped single-source, late-entry prevention;
- source quality: 1 source vs 2+ source entries;
- duplicate and stale-event prevention counters.

Dynamic behavior must be bounded and gradual. The system may adjust allocation caps, WAIT/ENTER thresholds, and source requirements based on multiple settled observations. It must not silently loosen safety rules after one lucky win. Changes should be logged as policy adjustments with before/after thresholds and reason.

## Safety rule

All of this remains paper-only:

- no real money;
- no sportsbook login;
- no account actions;
- no betting buttons;
- no deposits;
- no trading.

The contour evaluates agents with virtual credits only.
