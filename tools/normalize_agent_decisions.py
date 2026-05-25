#!/usr/bin/env python3
import csv
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/root/openclaw/workspace/aitestarena")
CSV = ROOT / "aitestarena_watchlist_outbox" / "agent_decisions.csv"
REJECT = ROOT / "aitestarena_watchlist_outbox" / "agent_decisions.rejected_by_normalizer.csv"
RECORDER = Path("/root/aitestarena/tools/record_agent_decision.py")

VALID = {"ENTER", "WAIT", "SKIP"}
MAP = {
    "NEEDS_SECOND_SOURCE": "WAIT",
    "CONFIRMED_LINE": "WAIT",
    "MODEL_CHECKED": "WAIT",
    "EXPIRED_SECOND_SOURCE": "SKIP",
    "NO_VALUE": "SKIP",
    "NO_ENTRY": "SKIP",
    "RESOLVED_PAPER_WIN": "SKIP",
    "RESOLVED_PAPER_LOSS": "SKIP",
}

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def clean_status(v):
    return (v or "").strip().upper()

def pick(row, *names):
    for name in names:
        v = row.get(name)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return ""

def normalize_dict_row(row):
    # Direct runner wide schema normally has event_id, market, status, reason, ...
    raw_status = clean_status(pick(row, "decision", "status", "decision_status"))
    decision = MAP.get(raw_status, raw_status)

    agent_id = pick(row, "agent_id") or "deepseek"
    event_id = pick(row, "event_id", "event")
    reason = pick(row, "reason", "rationale", "line_movement_note")

    if raw_status in MAP:
        reason = f"{raw_status}: {reason}"

    allocation = pick(row, "allocation", "suggested_paper_allocation", "stake")
    ts = pick(row, "ts", "created_at_utc", "timestamp") or now()

    if decision != "ENTER":
        allocation = "0"

    return {
        "agent_id": agent_id,
        "event_id": event_id,
        "decision": decision,
        "allocation": allocation or "0",
        "reason": reason,
        "ts": ts,
        "raw_status": raw_status,
    }

def normalize_positional_row(row):
    # Backward-compatible fallback for old canonical rows:
    # agent_id,event_id,decision,allocation,reason,ts
    if len(row) >= 6 and clean_status(row[2]) in VALID:
        agent_id, event_id, decision, allocation, reason, ts = row[:6]
        decision = clean_status(decision)
    elif len(row) >= 4 and clean_status(row[2]) in MAP:
        agent_id = "deepseek"
        event_id = row[0]
        raw = clean_status(row[2])
        decision = MAP[raw]
        allocation = "0"
        reason = f"{raw}: {row[3]}"
        ts = row[-1] if row[-1] else now()
    else:
        raise ValueError("REJECT_BAD_FORMAT")

    if decision != "ENTER":
        allocation = "0"

    return {
        "agent_id": agent_id or "deepseek",
        "event_id": event_id,
        "decision": decision,
        "allocation": allocation or "0",
        "reason": reason or "",
        "ts": ts or now(),
        "raw_status": decision,
    }

rows = []
reject = []
clean = []
seen = set()

if CSV.exists() and CSV.stat().st_size > 0:
    text = CSV.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if text:
        sample = text[0].lower()
        looks_header = ("event_id" in sample and ("status" in sample or "decision" in sample)) or sample.startswith("agent_id,")
        if looks_header:
            with CSV.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            mode = "dict"
        else:
            with CSV.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            mode = "positional"
    else:
        mode = "empty"
else:
    mode = "missing_or_empty"

for row in rows:
    try:
        item = normalize_dict_row(row) if isinstance(row, dict) else normalize_positional_row(row)
    except Exception as e:
        reject.append((list(row.values()) if isinstance(row, dict) else row) + [f"REJECT_PARSE:{type(e).__name__}"])
        continue

    agent_id = "deepseek"
    event_id = item["event_id"]
    decision = clean_status(item["decision"])
    allocation = item["allocation"]
    reason = item["reason"]
    ts = item["ts"]

    if not event_id:
        reject.append((list(row.values()) if isinstance(row, dict) else row) + ["REJECT_MISSING_EVENT_ID"])
        continue

    if decision not in VALID:
        reject.append((list(row.values()) if isinstance(row, dict) else row) + [f"REJECT_BAD_DECISION:{decision}"])
        continue

    if decision != "ENTER":
        allocation = "0"

    cmd = [
        "python3", str(RECORDER),
        "--agent-id", agent_id,
        "--event-id", event_id,
        "--decision", decision,
        "--allocation", allocation or "0",
        "--reason", reason or "",
        "--dry-run",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)

    if proc.returncode != 0:
        reject.append((list(row.values()) if isinstance(row, dict) else row) + [proc.stderr.strip()[:500]])
        continue

    key = (agent_id, event_id, decision, reason[:120])
    if key in seen:
        continue
    seen.add(key)
    clean.append([agent_id, event_id, decision, allocation or "0", reason[:500], ts])

# AITESTARENA_NORMALIZER_WRITES_HEADER_20260525
with CSV.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["agent_id", "event_id", "decision", "allocation", "reason", "created_at_utc"])
    w.writerows(clean)

with REJECT.open("w", encoding="utf-8", newline="") as f:
    csv.writer(f).writerows(reject)

print(f"normalizer_mode: {mode}")
print(f"normalized_kept: {len(clean)}")
print(f"normalized_rejected: {len(reject)}")
print(f"reject_file: {REJECT}")
