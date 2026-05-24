#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path("/root/aitestarena")
AGENTS = ["deepseek", "silent-gpt-5-5", "gpt-mini"]

def utc_iso():
    return datetime.now(timezone.utc).isoformat()

def ts():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}

def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"_raw": line[:500], "_parse_error": True})
    return rows

def result_of(row):
    for key in ("settlement_outcome", "result", "settlement", "status", "outcome"):
        v = row.get(key)
        if isinstance(v, str) and v:
            return v.upper()
    return "UNKNOWN"

def pnl_of(row):
    for key in ("pnl", "profit_loss", "realized_pnl", "net_pnl"):
        try:
            return float(row.get(key))
        except Exception:
            pass
    return 0.0

def lesson(counts, pnl, open_count, settled_count):
    wins = counts.get("WIN", 0)
    losses = counts.get("LOSS", 0)
    voids = counts.get("VOID", 0) + counts.get("VOID_NO_ENTRY", 0)

    if settled_count == 0:
        return "No settled sample yet; keep ENTER rare and conservative."
    if open_count > 0:
        return "Open positions exist; avoid duplicate exposure until settlement."
    if losses > wins and pnl < 0:
        return "Negative sample; tighten ENTER criteria and require clearer source/market confirmation."
    if voids > wins + losses and voids > 0:
        return "Too many voids; avoid unclear resolution/source paths."
    if wins > losses and pnl > 0:
        return "Positive sample; keep similar filters but do not raise allocation yet."
    return "Mixed sample; keep allocation capped and improve event clarity."

agents = []
total_counts = Counter()
total_pnl = 0.0

for aid in AGENTS:
    base = ROOT / "agents" / aid
    bankroll = load_json(base / "bankroll.json")
    decisions = load_jsonl(base / "decisions.jsonl")
    opened = load_jsonl(base / "positions_open.jsonl")
    settled = load_jsonl(base / "positions_settled.jsonl")

    counts = Counter(result_of(r) for r in settled)
    pnl = sum(pnl_of(r) for r in settled)
    total_counts.update(counts)
    total_pnl += pnl

    agents.append({
        "agent_id": aid,
        "decisions_count": len(decisions),
        "open_count": len(opened),
        "settled_count": len(settled),
        "settled_results": dict(counts),
        "settled_pnl_sum_from_rows": round(pnl, 4),
        "bankroll": {
            "available_bankroll": bankroll.get("available_bankroll"),
            "current_bankroll": bankroll.get("current_bankroll"),
            "reserved_open": bankroll.get("reserved_open"),
            "realized_pnl": bankroll.get("realized_pnl"),
            "total_bankroll": bankroll.get("total_bankroll"),
        },
        "last_settled": settled[-1] if settled else None,
        "selection_lesson": lesson(counts, pnl, len(opened), len(settled)),
    })

payload = {
    "schema": "aitestarena.agent_paper_results_analysis.v1",
    "generated_at_utc": utc_iso(),
    "mode": "read_only_analysis_no_state_mutation",
    "paper_only": True,
    "agents": agents,
    "summary": {
        "agents_count": len(agents),
        "total_settled_result_counts": dict(total_counts),
        "total_pnl_sum_from_rows": round(total_pnl, 4),
        "has_open_positions": any(a["open_count"] > 0 for a in agents),
    },
    "global_lesson": "Use settled paper results to tighten future ENTER criteria. Do not rewrite history or edit bankroll directly.",
}

state = ROOT / "state" / "agent_paper_results_latest.json"
report = ROOT / "reports" / f"agent_paper_results_{ts()}.json"

state.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("RESULTS_ANALYSIS_OK")
print("state:", state)
print("report:", report)
for a in agents:
    print(a["agent_id"], "decisions", a["decisions_count"], "open", a["open_count"], "settled", a["settled_count"], "realized_pnl", a["bankroll"]["realized_pnl"])
