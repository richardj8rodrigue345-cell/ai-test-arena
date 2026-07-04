# Writer-Stalker Handoff Guard

Updated: 2026-07-04
Status: ACTIVE

Checks:
REQUESTED without IN_PROGRESS >6h = WARN
IN_PROGRESS without DONE >24h = WARN
DONE without WRITER_ACK >24h = WARN
DRAFT without package at slot <24h = WARN
READY plus HOLD contradiction = FAIL
Package READY without approval = FAIL
Host check instead of container workspace = TOOL_CHECK_FALSE_NEGATIVE / WARN
