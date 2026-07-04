# OpenClaw — NotebookLM Active Source — 2026-07-04

Use this single file as the active source of truth for the current OpenClaw dashboard / Writer-Stalker-Sentinel / Codex work.

GitHub source folder:

https://github.com/richardj8rodrigue345-cell/ai-test-arena/tree/openclaw-dashboard-context-20260704-075836/docs/openclaw_dashboard_context/20260704-075836

Repository:

- repo: `richardj8rodrigue345-cell/ai-test-arena`
- branch: `openclaw-dashboard-context-20260704-075836`
- folder: `docs/openclaw_dashboard_context/20260704-075836/`

## 1. Current active contour

The current active OpenClaw editorial/dashboard contour is:

```text
Writer → Stalker → Writer ACK → Publish Package → Owner Approval → Sentinel/Controller Guard
```

This is a psychology-channel / editorial workflow contour, not the old AITestArena betting or paper-cycle contour.

## 2. Source-of-truth paths

Runtime source of truth for agents is container-local:

```text
/home/node/.openclaw/workspace/
```

Important agent workspaces:

```text
/home/node/.openclaw/workspace/writer/
/home/node/.openclaw/workspace/sentinel/
```

Host `/root/openclaw/...` is the operator/ops layer only. If a host check cannot see a file that exists inside the container workspace, classify it as `TOOL_CHECK_FALSE_NEGATIVE`, not as a missing agent file.

## 3. Current important files in this snapshot

The public-safe snapshot contains these real files, all under:

```text
docs/openclaw_dashboard_context/20260704-075836/
```

Important files:

```text
CURRENT_SYSTEM_SUMMARY.md
NOTEBOOKLM_PROMPT.md
README_CODEX_CONTEXT.md
writer/docs/WRITER_STALKER_HANDOFF_PROTOCOL.md
writer/state/TASK_REGISTRY.md
writer/state/publication_board.md
writer/tasks/STALKER_CURRENT_TASK.md
writer/tasks/WRITER_CURRENT_TASK.md
writer/inbox/stalker/TASK_WRITER-STALKER-20260704-001.md
writer/outbox/stalker/README.md
sentinel/docs/WRITER_STALKER_HANDOFF_GUARD.md
writer/dashboard/OPENCLAW_PATH_MAP.md
writer/docs/PUBLISH_GATE_PROTOCOL.md
writer/docs/PUBLISH_PACKAGE_PROTOCOL.md
writer/publish_packages/Q5_dobrota_k_sebe_20260705/GATE_STATE.md
writer/publish_packages/Q5_dobrota_k_sebe_20260705/approval.md
writer/publish_packages/Q5_dobrota_k_sebe_20260705/CHANGELOG.md
```

Do not invent JSON/YAML replacements such as `TASK_REGISTRY.json`, `STALKER_CURRENT_TASK.json`, `OWNER_APPROVAL.json`, or `dashboard_layout.yaml`. The current snapshot uses the Markdown files listed above.

## 4. Current Writer-Stalker task

Active task:

```text
TASK_ID: WRITER-STALKER-20260704-001
```

Task file:

```text
writer/inbox/stalker/TASK_WRITER-STALKER-20260704-001.md
```

Current expected state:

```text
STATUS: REQUESTED
TARGET_AGENT: STALKER
OUTPUT_PATH: writer/outbox/stalker/BRIEF_WRITER-STALKER-20260704-001.md
WRITER_ACK_REQUIRED: true
```

Expected Stalker output:

```text
writer/outbox/stalker/BRIEF_WRITER-STALKER-20260704-001.md
```

## 5. Main P0 defect

### P0: MISSING_STALKER_TRIGGER

Symptom:

Writer creates a task with `STATUS: REQUESTED`; `TASK_REGISTRY.md` contains the task; but Stalker does not automatically pick it up. `STALKER_CURRENT_TASK.md` remains `IDLE` / `TASK_ID: none`.

Observed cause:

No watcher, poller, cron, heartbeat, or session trigger guarantees this transition:

```text
REQUESTED → IN_PROGRESS
```

Expected dashboard behavior:

The dashboard must not simply report `WAITING_STALKER` when no trigger exists. It must report:

```text
MISSING_STALKER_TRIGGER
MANUAL_START_REQUIRED
```

or an equivalent FAIL/P0 status.

## 6. Current Q5 publish package state

Q5 package exists:

```text
writer/publish_packages/Q5_dobrota_k_sebe_20260705/
```

The gate state is intentionally not publishable without owner approval:

```text
STATE: PENDING_OWNER_APPROVAL
READY_TO_PUBLISH: false
PUBLISH_ALLOWED: false
PUBLISH_APPROVED: false
OWNER_APPROVAL_REQUIRED: true
```

No tool, script, agent, dashboard, or Codex patch may set approval automatically.

## 7. Non-negotiable rules

Codex and all agents must obey:

```text
- No auto approval.
- Never set PUBLISH_APPROVED: true.
- Never set READY_TO_PUBLISH without explicit owner approval.
- Never publish to Telegram.
- Never revive the old AITestArena betting/public training contour.
- Never treat /root/openclaw as agent source of truth.
- Never put secrets, tokens, raw sessions, or giant logs into dashboard.
- Keep dashboard compact.
- Use container workspace paths as truth.
- If host check contradicts container check, classify as TOOL_CHECK_FALSE_NEGATIVE.
```

## 8. Parked / legacy context

The old AITestArena betting / odds / paper-cycle / public training context is parked for this dashboard task. It must not be used as the active system model.

Do not use old terms or flows as current truth for this work:

```text
ENTER / WAIT / SKIP
odds
bankroll
settlement
paper betting cycle
07-cycle
old HEARTBEAT as active trigger
AITestArena public training / betting contour
```

Historical files may be useful for background only, but if they conflict with this source, this source wins.

## 9. Target dashboard blocks

The dashboard should have compact blocks:

### Writer-Stalker Handoff Guard

Indicators:

```text
pending_stalker_requests
requested_without_trigger
stalker_current_task
stale_stalker_tasks
last_stalker_brief
writer_ack_missing
outbox_brief_expected
outbox_brief_exists
```

Statuses:

```text
OK
WAITING_STALKER
MISSING_STALKER_TRIGGER
STALKER_IN_PROGRESS
BRIEF_DONE_WAITING_WRITER_ACK
HANDOFF_COMPLETE
FAIL
```

### Queue Freshness Guard

Checks:

```text
nearest slot
DRAFT without package
READY without approval
stale brief
board/package mismatch
```

### Publish Gate Guard

Checks:

```text
package state
approval.md
GATE_STATE.md
prepub_audit
HOLD contradiction
owner approval mark
```

### Tool Failure Guard

Checks:

```text
last failed tool/check
false negative due to host/container mismatch
stale lock
failed command
recovered failure
hidden failure
```

### Runtime / Container Workspace Guard

Checks:

```text
container workspace checked
host/root check detected
docker exec bridge available
snapshot age
source-of-truth path
```

### AITestArena Parked Status

Must show:

```text
PARKED
Do not revive betting/public training contour unless explicit owner command.
```

### Next Slot Readiness

Checks:

```text
next post
draft exists
package exists
owner approval state
publish allowed true/false
blocker reason
```

## 10. Required Codex implementation brief

Prepare Codex tasks in this structure:

```text
1. Current System Map
2. Broken Links / Defects
3. Target Dashboard Blocks
4. Implementation Plan for Codex
5. Non-Negotiable Rules
6. Acceptance Tests
7. P0/P1/P2 task list
```

For each defect/task include:

```text
defect_id or task_id
title
symptom
evidence files
expected behavior
actual behavior
severity: P0 / P1 / P2
proposed fix
acceptance test
rollback note
```

## 11. Required defects to include

### P0-1: MISSING_STALKER_TRIGGER

Writer creates `REQUESTED` task, but Stalker does not automatically pick it up.

### P0-2: Dashboard must distinguish WAITING_STALKER from MISSING_STALKER_TRIGGER

If no trigger exists, dashboard must not say only “waiting”. It must show P0/manual-start/trigger failure.

### P1-1: TASK_REGISTRY lacks WRITER_ACK field

Need a visible ACK state or registry field.

### P1-2: stale TASK-001 / stale inbox desync

Closed/DONE task must not remain active/open.

### P1-3: DRAFT → PACKAGE handoff

If board row is DRAFT and slot is less than 24h away, dashboard should warn unless package exists.

### P1-4: Tool false negatives due to host/container mismatch

Host checks can miss container-local files. Dashboard must classify this as `TOOL_CHECK_FALSE_NEGATIVE`.

### P2: compact dashboard / no raw dumps

Dashboard should summarize, not dump long logs.

## 12. Acceptance tests

Codex brief must define acceptance tests for:

```text
1. REQUESTED task with no trigger → MISSING_STALKER_TRIGGER / FAIL.
2. REQUESTED task with Stalker IN_PROGRESS → STALKER_IN_PROGRESS.
3. IN_PROGRESS without DONE >24h → WARN.
4. DONE brief exists without WRITER_ACK >24h → WARN.
5. DRAFT with slot <24h and no package → WARN.
6. Package exists but approval false → PENDING_OWNER_APPROVAL, publish not allowed.
7. READY + HOLD contradiction → FAIL.
8. Host cannot see container file but container can → TOOL_CHECK_FALSE_NEGATIVE.
9. AITestArena parked → PARKED, no old contour resurrection.
10. Dashboard rendering → compact blocks, no raw logs.
```

## 13. First response rule for NotebookLM

Before producing the Codex brief, first list the real files from this snapshot that you used. They must be real paths under:

```text
docs/openclaw_dashboard_context/20260704-075836/
```

If you cannot read the snapshot files, answer:

```text
SNAPSHOT_FILES_NOT_READABLE
```

Do not invent file names.

## 14. Short prompt to use with NotebookLM

Use only this file and the files in the same snapshot folder as active truth. Ignore old selected sources if they conflict with this file. Prepare Codex implementation brief for OpenClaw dashboard, Writer-Stalker handoff guard, Stalker trigger detection, publish gate guard, source-of-truth path guard, and AITestArena parked status.
