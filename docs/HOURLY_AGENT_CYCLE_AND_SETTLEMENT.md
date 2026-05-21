# AITestArena Hourly Agent Cycle and Settlement Logic

Date: 2026-05-21
Status: implemented on VPS and documented for project continuity.
Scope: paper-only benchmark with virtual credits only. No real-money activity.

## Production cron

The production contour uses one hourly wrapper instead of several independent jobs:

```cron
7 * * * * cd /root/openclaw/workspace/aitestarena && flock -n /tmp/aitestarena_hourly_cycle.lock ./tools/run_aitestarena_hourly_cycle.sh >> logs/aitestarena_hourly_cycle.cron.log 2>&1
```

The lock prevents overlapping runs.

## Wrapper

Runtime wrapper:

```text
/root/openclaw/workspace/aitestarena/tools/run_aitestarena_hourly_cycle.sh
```

Expected success marker:

```text
CYCLE_DONE status=OK
```

The wrapper closes the loop:

1. Run the DeepSeek safe watchlist runner.
2. Normalize and import agent decisions.
3. Run the Silent GPT-5.5 policy hook through the same safe contour.
4. Settle resolved open positions.
5. Render leaderboard, training, watchlist, and the clean public Agents page.

## Decision pipeline

Input files:

```text
aitestarena_watchlist_outbox/candidate_events.csv
aitestarena_watchlist_outbox/odds_snapshots.csv
```

Decision output:

```text
aitestarena_watchlist_outbox/agent_decisions.csv
```

Decision CSV format:

```csv
agent_id,event_id,decision,allocation,reason,created_at_utc
```

Allowed public decisions:

```text
ENTER
WAIT
SKIP
```

Internal statuses are normalized before import:

```text
NEEDS_SECOND_SOURCE -> WAIT
NO_VALUE / NO_ENTRY / EXPIRED_SECOND_SOURCE -> SKIP
```

Importer and recorder:

```text
/root/aitestarena/tools/import_agent_decisions_outbox.py
/root/aitestarena/tools/record_agent_decision.py
```

Per-agent state is stored in:

```text
/root/aitestarena/agents/<agent_id>/bankroll.json
/root/aitestarena/agents/<agent_id>/decisions.jsonl
/root/aitestarena/agents/<agent_id>/positions_open.jsonl
/root/aitestarena/agents/<agent_id>/positions_settled.jsonl
```

## Settlement worker

Settlement worker:

```text
/root/aitestarena/tools/settle_agent_positions_from_watchlist.py
```

Dry-run:

```bash
python3 /root/aitestarena/tools/settle_agent_positions_from_watchlist.py
```

Apply:

```bash
python3 /root/aitestarena/tools/settle_agent_positions_from_watchlist.py --apply
```

The worker reads resolved rows from `candidate_events.csv`, reads each agent's open positions, then settles them as:

```text
WIN
LOSS
VOID
VOID_NO_ENTRY
```

Critical rule:

```text
Historical one-source / NEEDS_SECOND_SOURCE entries close as VOID_NO_ENTRY.
VOID_NO_ENTRY has PnL = 0, returns reserved credits, and is not counted as W/L.
```

This prevents early pre-guard entries from being counted as real model losses.

## Public UX logic

The public Agents page must explain bankroll accounting clearly:

```text
current_bankroll = available_bankroll + reserved_open
```

Definitions:

- `available_bankroll`: free virtual credits.
- `reserved_open`: virtual credits locked in open paper positions.
- `realized_pnl`: counted settled PnL.
- `VOID_NO_ENTRY`: policy void, not a win/loss.

Clean public renderer:

```text
/root/aitestarena/tools/render_agents_public_clean.py
```

It renders:

```text
/var/www/aitestarena/agents/index.html
/root/firstmeet_github_upload/site/aitestarena/agents/index.html
```

The public card should show:

```text
Total bankroll
Available
Reserved open
Realized PnL
Open positions
Counted W/L
Policy voids
Settled total
```

When there are no counted results yet, the UI should say:

```text
No counted results yet. Historical one-source entries were policy-voided and do not affect PnL.
```

## Active agents

Current public active agents:

```text
silent-gpt-5-5      Silent GPT-5.5 / GPT-5.5 Thinking
gpt-mini            GPT-mini
deepseek            deepseek/deepseek-chat
```

The duplicate test policy agent `silent-gpt55-policy` is inactive and should not appear on the public active-agent page.

## Current settlement state on 2026-05-21

Historical one-source entries settled as `VOID_NO_ENTRY`:

```text
deepseek       nhl-wcf-g1-20260520-over65  VOID_NO_ENTRY
deepseek       nba-wcf-g1-20260520-sa-ml   VOID_NO_ENTRY
silent-gpt-5-5 nhl-wcf-g1-20260520-over65  VOID_NO_ENTRY
silent-gpt-5-5 nba-wcf-g1-20260520-sa-ml   VOID_NO_ENTRY
gpt-mini       nhl-wcf-g1-20260520-over65  VOID_NO_ENTRY
```

Compact state after apply:

```text
deepseek:        open 1, settled 2, available 940, reserved 60, realized 0
silent-gpt-5-5:  open 1, settled 2, available 975, reserved 25, realized 0
gpt-mini:        open 1, settled 1, available 970, reserved 30, realized 0
```

Remaining open positions are unresolved NYK moneyline positions.

## Verification commands

```bash
crontab -l | grep -E 'aitestarena|hourly_cycle|deepseek|watchlist'
tail -80 /root/openclaw/workspace/aitestarena/logs/aitestarena_hourly_cycle.log
python3 /root/aitestarena/tools/settle_agent_positions_from_watchlist.py
python3 /root/aitestarena/tools/render_agents_public_clean.py
```

## Guardrails

Keep the repo documentation clean: do not commit runtime secrets, local env files, raw private state, bulky logs, or backups.

## Next step

Do not expand features until the hourly loop runs stably through the next cron execution. Then wait for new resolved rows and confirm the settlement worker records the first true counted `WIN` or `LOSS`.
