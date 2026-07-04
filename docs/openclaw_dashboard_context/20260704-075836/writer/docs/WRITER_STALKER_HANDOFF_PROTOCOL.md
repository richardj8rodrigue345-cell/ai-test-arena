# Writer-Stalker-Controller Handoff Protocol

Updated: 2026-07-04
Status: ACTIVE

## Canonical workspace

Agent source of truth is inside container:

/home/node/.openclaw/workspace/writer/

Host /root/openclaw is operator/ops layer only.

## Expected flow

1. Writer creates request:
   writer/inbox/stalker/TASK_<id>.md
   STATUS: REQUESTED

2. Stalker accepts:
   writer/tasks/STALKER_CURRENT_TASK.md
   STATUS: IN_PROGRESS

3. Stalker returns brief:
   writer/outbox/stalker/BRIEF_<id>.md
   STATUS: DONE

4. Writer acknowledges:
   WRITER_ACK: true
   ACK_DATE:
   ACK_EVIDENCE:

5. Writer updates draft and board.

6. If board row is DRAFT and slot <24h:
   Writer/Packager must create publish_package.
   Initial state must be PENDING_OWNER_APPROVAL.
   Never READY_TO_PUBLISH without owner approval.

## Controller checks

REQUESTED without IN_PROGRESS >6h = WARN
IN_PROGRESS without DONE >24h = WARN
DONE without WRITER_ACK >24h = WARN
DRAFT without package at slot <24h = WARN
READY plus HOLD contradiction = FAIL
Package READY without approval = FAIL
Host check instead of container workspace = TOOL_CHECK_FALSE_NEGATIVE / WARN

## Dashboard block

Title: Writer-Stalker Handoff Guard

Indicators:
pending_stalker_requests
stale_stalker_tasks
last_stalker_brief
writer_ack_missing
drafts_without_package
package_pending_approval
gate_contradictions
container_workspace_checked

## Q5 lesson

Q5 draft existed only inside container workspace.
Host/root diagnostics could not see it.
Q5 package was created inside container and left PENDING_OWNER_APPROVAL.
