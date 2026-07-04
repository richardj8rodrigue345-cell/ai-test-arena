# OpenClaw Current System Summary — 2026-07-04

This is a public-safe context pack for NotebookLM/Codex.

## Active source of truth

Container workspace:

/home/node/.openclaw/workspace/

Host /root/openclaw is operator/ops layer only.

## Active contour

Writer → Stalker → Writer ACK → Publish Package → Owner Approval → Sentinel/Controller Guard

## Current known state

- Q5 package exists and is PENDING_OWNER_APPROVAL.
- No auto approval is allowed.
- No READY_TO_PUBLISH without explicit owner approval.
- Writer-Stalker handoff protocol exists.
- Current task WRITER-STALKER-20260704-001 exists and is REQUESTED.
- Expected Stalker output path:
  writer/outbox/stalker/BRIEF_WRITER-STALKER-20260704-001.md
- Sentinel/Controller detected P0: MISSING_STALKER_TRIGGER.

## P0 defect

MISSING_STALKER_TRIGGER:
Writer can create a REQUESTED task, but Stalker has no automatic trigger/poller/heartbeat to pick it up.

Dashboard must not show only WAITING_STALKER when no trigger exists. It must show MISSING_STALKER_TRIGGER / MANUAL_START_REQUIRED.
