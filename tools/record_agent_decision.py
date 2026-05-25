#!/usr/bin/env python3
import argparse, json, subprocess
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("/root/aitestarena")
AGENTS = BASE / "agents"
WATCHLIST = Path("/var/www/aitestarena/data/watchlist.json")

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# AITESTARENA_RECORD_LOOKUP_FALLBACK_20260525
def find_event(event_id):
    data = load_json(WATCHLIST, {})
    pools = []

    if isinstance(data, dict):
        for key in ("cards", "items", "events", "watchlist"):
            if isinstance(data.get(key), list):
                pools.extend(data.get(key) or [])
    elif isinstance(data, list):
        pools.extend(data)

    for e in pools:
        if isinstance(e, dict) and e.get("event_id") == event_id:
            return e

    active_json = BASE / "watchlist" / "active" / f"{event_id}.json"
    e = load_json(active_json, {})
    if isinstance(e, dict) and e:
        e.setdefault("event_id", event_id)
        return e

    cand_csv = Path("/root/openclaw/workspace/aitestarena/aitestarena_watchlist_outbox/candidate_events.csv")
    if cand_csv.exists():
        import csv
        with cand_csv.open(encoding="utf-8-sig", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("event_id") == event_id:
                    return dict(row)

    raise SystemExit(f"event_id not found in watchlist: {event_id}")

def ensure_agent(agent_id):
    reg = load_json(AGENTS / "registry.json", {})
    ids = {a.get("agent_id") for a in reg.get("agents", []) if a.get("status") == "active"}
    if agent_id not in ids:
        raise SystemExit(f"agent_id is not active in registry: {agent_id}")

    d = AGENTS / agent_id
    d.mkdir(parents=True, exist_ok=True)

    bankroll_path = d / "bankroll.json"
    if not bankroll_path.exists():
        save_json(bankroll_path, {
            "schema": "aitestarena.agent_bankroll.v1",
            "agent_id": agent_id,
            "mode": "paper_only",
            "currency": "virtual_credits",
            "starting_bankroll": 1000.0,
            "current_bankroll": 1000.0,
            "available_bankroll": 1000.0,
            "reserved_open": 0.0,
            "realized_pnl": 0.0,
            "open_positions_count": 0,
            "settled_positions_count": 0,
            "bets_count": 0,
            "enter_count": 0,
            "wait_count": 0,
            "skip_count": 0,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "safety_note": "No real money. No betting. No trading. Virtual credits only."
        })

    for name in ["decisions.jsonl", "positions_open.jsonl", "positions_settled.jsonl"]:
        (d / name).touch(exist_ok=True)

    perf_path = d / "performance.json"
    if not perf_path.exists():
        save_json(perf_path, {
            "schema": "aitestarena.agent_performance.v1",
            "agent_id": agent_id,
            "bankroll_curve": [
                {"ts": datetime.now(timezone.utc).isoformat(), "bankroll": 1000.0, "note": "initial"}
            ],
            "metrics": {
                "paper_pnl": 0.0,
                "roi": 0.0,
                "open_positions": 0,
                "settled_positions": 0,
                "win_rate": None,
                "avg_clv": None,
                "brier": None,
                "discipline_score": None
            }
        })

    return d

def count_jsonl(path):
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()) if path.exists() else 0

ap = argparse.ArgumentParser()
ap.add_argument("--agent-id", required=True)
ap.add_argument("--event-id", required=True)
ap.add_argument("--decision", required=True, choices=["ENTER", "WAIT", "SKIP"])
ap.add_argument("--allocation", type=float, default=0.0)
ap.add_argument("--reason", default="")
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args()

ensure_agent(args.agent_id)
event = find_event(args.event_id)
agent_dir = AGENTS / args.agent_id

bankroll_path = agent_dir / "bankroll.json"
bankroll = load_json(bankroll_path, {})

allocation = float(args.allocation)
if args.decision != "ENTER":
    allocation = 0.0

available = float(bankroll.get("available_bankroll", 1000.0))
if args.decision == "ENTER":
    if allocation <= 0:
        raise SystemExit("ENTER requires allocation > 0")
    if allocation > available:
        raise SystemExit(f"allocation exceeds available bankroll: {allocation} > {available}")

ts = datetime.now(timezone.utc).isoformat()

record = {
    "schema": "aitestarena.agent_decision.v1",
    "ts": ts,
    "agent_id": args.agent_id,
    "event_id": args.event_id,
    "event": event.get("event"),
    "sport": event.get("sport"),
    "market": event.get("market"),
    "decision": args.decision,
    "allocation": allocation,
    "entry_odds": event.get("best_decimal_odds"),
    "bookmaker": event.get("best_bookmaker"),
    "breakeven_probability": event.get("breakeven_probability"),
    "estimated_fair_probability": event.get("estimated_fair_probability"),
    "ev": event.get("ev"),
    "decision_status_at_entry": event.get("decision_status"),
    "line_movement_note": event.get("line_movement_note"),
    "source_url": event.get("source_url"),
    "reason": args.reason,
    "paper_only": True,
    "safety_note": "No real money. No betting. No trading. Virtual credits only."
}

position = None
if args.decision == "ENTER":
    position = {
        **record,
        "schema": "aitestarena.agent_open_position.v1",
        "status": "open",
        "stake": allocation,
        "opened_at_utc": ts,
        "settlement_source": event.get("settlement_source")
    }

if args.dry_run:
    print(json.dumps({
        "dry_run": True,
        "would_record": record,
        "would_open_position": position
    }, ensure_ascii=False, indent=2))
    raise SystemExit(0)

append_jsonl(agent_dir / "decisions.jsonl", record)

if args.decision == "ENTER":
    append_jsonl(agent_dir / "positions_open.jsonl", position)
    bankroll["available_bankroll"] = round(available - allocation, 4)
    bankroll["reserved_open"] = round(float(bankroll.get("reserved_open", 0.0)) + allocation, 4)
    bankroll["bets_count"] = int(bankroll.get("bets_count", 0)) + 1
    bankroll["enter_count"] = int(bankroll.get("enter_count", 0)) + 1
elif args.decision == "WAIT":
    bankroll["wait_count"] = int(bankroll.get("wait_count", 0)) + 1
elif args.decision == "SKIP":
    bankroll["skip_count"] = int(bankroll.get("skip_count", 0)) + 1

bankroll["open_positions_count"] = count_jsonl(agent_dir / "positions_open.jsonl")
bankroll["settled_positions_count"] = count_jsonl(agent_dir / "positions_settled.jsonl")
bankroll["updated_at_utc"] = ts
save_json(bankroll_path, bankroll)

subprocess.run(["python3", "/root/aitestarena/tools/render_agents_leaderboard.py"], check=False)
if args.agent_id == "silent-gpt-5-5":
    subprocess.run(["python3", "/root/aitestarena/tools/render_silent_gpt55_training.py"], check=False)

print(json.dumps({
    "ok": True,
    "agent_id": args.agent_id,
    "event_id": args.event_id,
    "decision": args.decision,
    "allocation": allocation,
    "available_bankroll": bankroll.get("available_bankroll"),
    "reserved_open": bankroll.get("reserved_open")
}, ensure_ascii=False, indent=2))
