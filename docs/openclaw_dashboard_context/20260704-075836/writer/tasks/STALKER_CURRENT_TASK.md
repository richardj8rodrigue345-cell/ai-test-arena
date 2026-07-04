# STALKER CURRENT TASK

Updated: 2026-07-04
TASK_ID: none
STATUS: IDLE
LAST_BRIEF: none
LAST_BRIEF_AT:
WRITER_ACK_REQUIRED: false

Startup rule:
1. Check writer/state/TASK_REGISTRY.md
2. Check writer/inbox/stalker/
3. Check writer/tasks/open/

If REQUESTED task exists:
STATUS must become IN_PROGRESS.

When done:
Write brief to writer/outbox/stalker/BRIEF_<id>.md

Output limit:
Keep brief under 40 lines unless requested.
