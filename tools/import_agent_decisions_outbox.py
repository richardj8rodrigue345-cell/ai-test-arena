#!/usr/bin/env python3
import csv, json, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone

OUTBOX = Path("/root/openclaw/workspace/aitestarena/aitestarena_watchlist_outbox/agent_decisions.csv")
STATE = Path("/root/aitestarena/state")
PROCESSED = STATE / "agent_decisions_processed.jsonl"
AGENTS = Path("/root/aitestarena/agents")

STATE.mkdir(parents=True, exist_ok=True)

REQUIRED = ["agent_id", "event_id", "decision", "allocation", "reason", "created_at_utc"]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean(x):
    return str(x or "").strip()

def read_processed():
    seen = set()
    if PROCESSED.exists():
        for line in PROCESSED.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                obj = json.loads(line)
                h = obj.get("hash")
                if h:
                    seen.add(h)
            except Exception:
                pass
    return seen

def row_hash(row):
    payload = {
        k: clean(row.get(k))
        for k in REQUIRED
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def append_processed(h, row, status, note=""):
    with PROCESSED.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": now_iso(),
            "hash": h,
            "status": status,
            "note": note,
            "agent_id": clean(row.get("agent_id")),
            "event_id": clean(row.get("event_id")),
            "decision": clean(row.get("decision")).upper(),
            "created_at_utc": clean(row.get("created_at_utc")),
        }, ensure_ascii=False) + "\n")

def open_position_exists(agent_id, event_id):
    p = AGENTS / agent_id / "positions_open.jsonl"
    if not p.exists():
        return False

    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue

        if clean(obj.get("event_id")) == event_id and clean(obj.get("status")) == "open":
            return True

    return False

def main():
    if not OUTBOX.exists():
        print("missing outbox:", OUTBOX)
        return 0

    rows = list(csv.DictReader(OUTBOX.open(encoding="utf-8-sig", newline="")))
    seen = read_processed()

    imported = 0
    skipped = 0
    errors = 0

    for row in rows:
        h = row_hash(row)

        if h in seen:
            skipped += 1
            continue

        missing = [k for k in REQUIRED if not clean(row.get(k))]
        if missing:
            errors += 1
            append_processed(h, row, "error", "missing: " + ",".join(missing))
            continue

        agent_id = clean(row.get("agent_id"))
        event_id = clean(row.get("event_id"))
        decision = clean(row.get("decision")).upper()

        # Critical guard:
        # Do not open a second active paper position for same agent + event.
        if decision == "ENTER" and open_position_exists(agent_id, event_id):
            skipped += 1
            append_processed(h, row, "skipped_duplicate_open_position", "open position already exists for agent_id + event_id")
            print("skip duplicate open:", agent_id, event_id)
            continue

        cmd = [
            "python3",
            "/root/aitestarena/tools/record_agent_decision.py",
            "--agent-id", agent_id,
            "--event-id", event_id,
            "--decision", decision,
            "--allocation", clean(row.get("allocation")),
            "--reason", clean(row.get("reason")),
        ]

        proc = subprocess.run(cmd, text=True, capture_output=True)

        if proc.returncode != 0:
            errors += 1
            append_processed(h, row, "error", (proc.stderr or proc.stdout)[-1000:])
            print("error:", agent_id, event_id, decision, (proc.stderr or proc.stdout)[-300:])
            continue

        imported += 1
        append_processed(h, row, "imported", "")

    print("imported:", imported)
    print("skipped:", skipped)
    print("errors:", errors)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
