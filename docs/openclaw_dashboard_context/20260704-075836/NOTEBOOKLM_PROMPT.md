# NotebookLM task

Use only this folder as source of truth:

docs/openclaw_dashboard_context/20260704-075836/

Do not use old AITestArena NotebookLM sources, old ENTER-WAIT-SKIP, odds, bankroll, settlement, 07-cycle, or heartbeat docs as the active current system.

Current active contour:

Writer → Stalker → Writer ACK → Publish Package → Owner Approval → Sentinel/Controller Guard

Known P0 defect:

MISSING_STALKER_TRIGGER

Symptom:
Writer creates a TASK with STATUS REQUESTED and TASK_REGISTRY contains it, but Stalker does not automatically pick it up. STALKER_CURRENT_TASK remains IDLE. There is no watcher/cron/heartbeat that guarantees REQUESTED → IN_PROGRESS.

Prepare a Codex implementation brief for:
- dashboard
- Writer-Stalker handoff guard
- Stalker trigger detection
- publish gate guard
- source-of-truth path guard
- AITestArena parked status

Before answering, list 10 files from this folder that you used.
