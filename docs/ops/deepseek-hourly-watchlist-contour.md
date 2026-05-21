# AITestArena — DeepSeek hourly watchlist contour

Date: 2026-05-21
Status: active / restored
Scope: AITestArena watchlist, paper-only benchmark, virtual credits

## Purpose

This document records the current DeepSeek hourly watchlist contour for AITestArena: how the server cron starts the flow, how DeepSeek is called, how model outputs are guarded, how raw service statuses are normalized, and how the agent/watchlist pages are refreshed without changing the main OpenClaw mini model.

This is a paper-only evaluation loop. It is used for model benchmarking, source-confirmation discipline, EV-style reasoning, and virtual-credit decisions. It must not perform external account actions or any real-world financial action.

## Working path

Current server path:

```text
/root/openclaw/workspace/aitestarena
```

Do not use the older path for current server operations:

```text
/home/node/.openclaw/workspace/aitestarena
```

## Architecture

Current flow:

```text
root crontab
→ tools/run_deepseek_watchlist_safe.sh --apply
→ direct_deepseek_runner.py
→ DeepSeek API direct call
→ aitestarena_watchlist_outbox/agent_decisions.csv
→ tools/normalize_agent_decisions.py
→ /root/aitestarena/tools/import_agent_decisions_outbox.py
→ /root/aitestarena/tools/render_agents_leaderboard.py
→ /root/aitestarena/tools/process_watchlist_outbox.py
```

This keeps the DeepSeek paper-agent workflow separate from the main OpenClaw Telegram/mini runtime.

## Cron

Installed root crontab entry:

```cron
7 * * * * cd /root/openclaw/workspace/aitestarena && flock -n /tmp/aitestarena_deepseek_direct_safe.lock ./tools/run_deepseek_watchlist_safe.sh --apply >> logs/deepseek_direct_safe.cron.log 2>&1
```

Meaning:

- runs once per hour on minute 7;
- changes into the correct workspace;
- uses `flock` to prevent overlapping runs;
- calls the safe wrapper only;
- writes cron-level logs to `logs/deepseek_direct_safe.cron.log`.

## Safe wrapper

Wrapper path:

```text
tools/run_deepseek_watchlist_safe.sh
```

Responsibilities:

1. Enter `/root/openclaw/workspace/aitestarena`.
2. Load local DeepSeek environment settings when present.
3. Write an hourly prompt marker into `logs/direct_deepseek_runner.safe.log`.
4. Copy `tasks/DEEPSEEK_WATCHLIST_HOURLY_PROMPT.md` to `tasks/DEEPSEEK_WATCHLIST_CURRENT_TASK.md` for auditability.
5. Run `direct_deepseek_runner.py`.
6. Run `tools/normalize_agent_decisions.py`.
7. Run the canonical import/render/process scripts from `/root/aitestarena/tools/`.
8. Leave a final `DONE` marker in the safe log.

Dry run:

```bash
tools/run_deepseek_watchlist_safe.sh
```

Apply run:

```bash
tools/run_deepseek_watchlist_safe.sh --apply
```

## Prompt/task files

Hourly prompt file:

```text
tasks/DEEPSEEK_WATCHLIST_HOURLY_PROMPT.md
```

Current task copy:

```text
tasks/DEEPSEEK_WATCHLIST_CURRENT_TASK.md
```

The markdown prompt is currently an audit/task declaration. The direct API prompt is still assembled by `direct_deepseek_runner.py` from:

```text
aitestarena_watchlist_outbox/candidate_events.csv
aitestarena_watchlist_outbox/odds_snapshots.csv
```

Later improvement: prepend or include the hourly markdown prompt in the actual API prompt.

## Direct DeepSeek runner

Runner path:

```text
direct_deepseek_runner.py
```

Responsibilities:

1. Read `candidate_events.csv`.
2. Read `odds_snapshots.csv`.
3. Select active candidates.
4. Build a compact context prompt.
5. Call DeepSeek directly.
6. Parse response.
7. Apply guard logic.
8. Append raw decision/status rows into `aitestarena_watchlist_outbox/agent_decisions.csv`.

Secrets are intentionally excluded from this document and from GitHub.

## Guard policy

The contour should only produce paper benchmark decisions. It should not perform external account actions.

The guard avoids `ENTER` unless all of the following are true:

- at least two independent sources confirm the same market;
- fair probability exists;
- EV is positive;
- Kelly is positive;
- event has not started and deadline has not expired;
- line is valid and directly comparable;
- allocation respects risk limits.

Single-source candidates should remain `WAIT` or a service status such as `NEEDS_SECOND_SOURCE`, later normalized.

Expired unconfirmed candidates should become `SKIP` with the reason stored as `EXPIRED_SECOND_SOURCE`.

Non-positive EV candidates should become `SKIP` with the reason stored as `NO_VALUE`.

## Normalizer

Normalizer path:

```text
tools/normalize_agent_decisions.py
```

Reason: the official import path accepts only:

```text
ENTER
WAIT
SKIP
```

The runner can produce service statuses such as:

```text
NEEDS_SECOND_SOURCE
EXPIRED_SECOND_SOURCE
NO_VALUE
NO_ENTRY
CONFIRMED_LINE
MODEL_CHECKED
RESOLVED_PAPER_WIN
RESOLVED_PAPER_LOSS
```

Mapping:

```text
NEEDS_SECOND_SOURCE   → WAIT
CONFIRMED_LINE        → WAIT
MODEL_CHECKED         → WAIT
EXPIRED_SECOND_SOURCE → SKIP
NO_VALUE              → SKIP
NO_ENTRY              → SKIP
RESOLVED_PAPER_WIN    → SKIP
RESOLVED_PAPER_LOSS   → SKIP
```

The normalizer also forces the agent id to the registered active id:

```text
deepseek
```

Before a row is allowed into the cleaned `agent_decisions.csv`, it is checked with:

```bash
python3 /root/aitestarena/tools/record_agent_decision.py --dry-run
```

Rejected rows go to:

```text
aitestarena_watchlist_outbox/agent_decisions.rejected_by_normalizer.csv
```

## Canonical import/render scripts

The wrapper runs:

```text
/root/aitestarena/tools/import_agent_decisions_outbox.py
/root/aitestarena/tools/render_agents_leaderboard.py
/root/aitestarena/tools/process_watchlist_outbox.py
```

The runner itself may still warn about missing local post-script paths under `/root/openclaw/workspace/aitestarena/`. These warnings are non-fatal because the wrapper runs the canonical paths afterward.

## Last verified healthy run

Last known healthy run showed:

```text
hourly prompt: tasks/DEEPSEEK_WATCHLIST_HOURLY_PROMPT.md
DeepSeek responded
runner_rc=0
normalize agent_decisions done
imported: 0
skipped: 14
errors: 0
agents rendered: 3
active: 3
rejected: 9
DONE
```

Success criterion:

```text
errors: 0
```

## Main OpenClaw model safety

The direct DeepSeek contour does not change the OpenClaw main model configuration.

Verified main primary model:

```text
openai/gpt-5.4-mini
```

DeepSeek remains a separate contour/model:

```text
deepseek/deepseek-chat
```

## Known technical debt

1. `direct_deepseek_runner.py` still tries to call wrong local post-script paths. The wrapper mitigates this.
2. Repeated hourly WAIT/SKIP rows can grow the CSV. Later improvement: keep latest per event/status family, plus append-only audit history.
3. The markdown hourly prompt is not yet the direct source of the API prompt.
4. Status vocabulary should be separated from official decisions: decision = ENTER/WAIT/SKIP; reason/status = NEEDS_SECOND_SOURCE, EXPIRED_SECOND_SOURCE, NO_VALUE, etc.

## Health check

After a cron run:

```bash
cd /root/openclaw/workspace/aitestarena || exit 1

echo "=== cron log ==="
tail -100 logs/deepseek_direct_safe.cron.log

echo "=== safe log ==="
tail -100 logs/direct_deepseek_runner.safe.log

echo "=== import clean check ==="
python3 /root/aitestarena/tools/import_agent_decisions_outbox.py
```

Expected:

```text
errors: 0
```

## Disable / rollback

Disable hourly direct contour:

```bash
crontab -l | grep -v 'run_deepseek_watchlist_safe.sh --apply' | crontab -
```

Backup cron before changing:

```bash
crontab -l > /root/openclaw/backups/root_crontab.before_deepseek_direct_disable_$(date -u +%Y%m%d_%H%M%S).txt 2>/dev/null || true
```

Restore cron:

```bash
crontab /root/openclaw/backups/<backup-file>.txt
```

## One-line summary

AITestArena now has a separate safe hourly DeepSeek watchlist contour: server cron runs a safe wrapper; the wrapper calls DeepSeek directly; guard logic prevents unsupported `ENTER`; the normalizer converts service statuses to ENTER/WAIT/SKIP; the official importer renders without errors; and the main OpenClaw mini model remains untouched.
