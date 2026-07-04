# Writer After Stalker Report Checklist

Updated: 2026-07-04

Required ACK fields:

WRITER_ACK: false
ACK_DATE:
ACK_EVIDENCE:
BRIEF_PATH:
AFFECTED_DRAFTS:
DECISION: ACCEPT / PARTIAL / REJECT / HOLD

Controller rule:
DONE without WRITER_ACK >24h = WARN
DONE without WRITER_ACK >48h = FAIL if next publication slot is affected
