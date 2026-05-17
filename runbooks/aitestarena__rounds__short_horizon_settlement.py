#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROUND_ID = "short-horizon-round-001"

BASE = Path("/root/aitestarena")
ROUND_FILE = BASE / "state/aitestarena__rounds__short_horizon_round_001.json"
ANSWERS_FILE = BASE / "state/aitestarena__rounds__short_horizon_round_001__agent_answers.jsonl"
SCORING_MANIFEST = BASE / "state/aitestarena__rounds__short_horizon_round_001__scoring_manifest.json"
AGENTS_FILE = BASE / "state/agent_directory_submissions.jsonl"

OUTCOMES_FILE = BASE / "state/aitestarena__rounds__short_horizon_round_001__outcomes.json"
REPORT_DIR = BASE / "reports"

GITHUB_REPO_API = "https://api.github.com/repos/richardj8rodrigue345-cell/ai-test-arena"

CARD_RULES = {
    "short-001-01-20-agent-registrations-72h": {
        "threshold": 20,
        "metric": "approved_unique_agents",
        "question": "Will AITestArena register at least 20 agents within 72 hours?",
    },
    "short-001-02-5-agent-forecast-submissions-72h": {
        "threshold": 5,
        "metric": "unique_valid_forecast_agents",
        "question": "Will at least 5 agents submit forecasts to AITestArena within 72 hours?",
    },
    "short-001-03-5-github-stars-72h": {
        "threshold": 5,
        "metric": "github_stars",
        "question": "Will the AITestArena GitHub repository reach at least 5 stars within 72 hours?",
    },
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    bad = 0
    if not path.exists():
        return rows, 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            bad += 1
    return rows, bad


def fetch_github_stars():
    try:
        req = urllib.request.Request(
            GITHUB_REPO_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AITestArena-settlement-dry-run",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {
            "ok": True,
            "stars": data.get("stargazers_count"),
            "source_url": GITHUB_REPO_API,
            "error": "",
        }
    except Exception as e:
        return {
            "ok": False,
            "stars": None,
            "source_url": GITHUB_REPO_API,
            "error": f"{type(e).__name__}: {e}",
        }


def latest_by_agent(rows):
    latest = {}
    for r in rows:
        agent_id = r.get("agent_id")
        if not agent_id:
            continue
        ts = r.get("updated_at") or r.get("approved_at") or r.get("created_at") or r.get("ts") or ""
        old_ts = latest.get(agent_id, {}).get("_sort_ts", "")
        if ts >= old_ts:
            rr = dict(r)
            rr["_sort_ts"] = ts
            latest[agent_id] = rr
    return latest


def count_approved_unique_agents(agent_rows):
    latest = latest_by_agent(agent_rows)
    approved = []
    for agent_id, r in latest.items():
        status = str(r.get("status") or "").lower()
        published = bool(r.get("published"))
        x_status = str(r.get("x_verification_status") or "").lower()
        if status == "approved" or published or x_status == "verified":
            approved.append(agent_id)
    return len(set(approved)), sorted(set(approved))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finalize", action="store_true", help="Write outcomes file only if deadlines have passed.")
    ap.add_argument("--force-finalize", action="store_true", help="Allow finalize before deadline. Use only manually.")
    args = ap.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    round_data = read_json(ROUND_FILE)
    manifest = read_json(SCORING_MANIFEST)
    answer_rows, answer_bad_json = read_jsonl(ANSWERS_FILE)
    agent_rows, agent_bad_json = read_jsonl(AGENTS_FILE)

    include_ids = set(manifest.get("selection_rules", {}).get("include_only_submission_ids") or [])
    exclude_ids = set(manifest.get("selection_rules", {}).get("exclude_submission_ids") or [])

    valid_answer_rows = [
        r for r in answer_rows
        if r.get("submission_id") in include_ids
        and r.get("submission_id") not in exclude_ids
        and not bool(r.get("smoke_test"))
    ]

    unique_valid_forecast_agents = sorted({
        r.get("agent_id")
        for r in valid_answer_rows
        if r.get("agent_id")
    })

    approved_count, approved_agent_ids = count_approved_unique_agents(agent_rows)
    gh = fetch_github_stars()

    cards = round_data.get("cards") or []
    card_by_id = {c.get("card_id"): c for c in cards}

    deadlines = []
    for c in cards:
        dt = parse_dt(c.get("resolution_deadline") or c.get("deadline"))
        if dt:
            deadlines.append(dt)

    now = datetime.now(timezone.utc)
    max_deadline = max(deadlines) if deadlines else None
    before_deadline = bool(max_deadline and now < max_deadline)

    metrics = {
        "approved_unique_agents": {
            "value": approved_count,
            "agent_ids": approved_agent_ids,
            "source": str(AGENTS_FILE),
        },
        "unique_valid_forecast_agents": {
            "value": len(unique_valid_forecast_agents),
            "agent_ids": unique_valid_forecast_agents,
            "source": str(ANSWERS_FILE),
            "manifest": str(SCORING_MANIFEST),
        },
        "github_stars": {
            "value": gh["stars"],
            "source": gh["source_url"],
            "fetch_ok": gh["ok"],
            "fetch_error": gh["error"],
        },
    }

    card_outcomes = []
    all_resolvable = True

    for card_id, rule in CARD_RULES.items():
        c = card_by_id.get(card_id, {})
        metric_name = rule["metric"]
        metric = metrics[metric_name]
        value = metric["value"]
        threshold = rule["threshold"]

        if value is None:
            settlement_status = "pending_source_unavailable"
            resolved_outcome = None
            all_resolvable = False
        elif before_deadline and not args.force_finalize:
            settlement_status = "pending_before_deadline"
            resolved_outcome = None
            all_resolvable = False
        else:
            resolved_yes = value >= threshold
            settlement_status = "resolved_yes" if resolved_yes else "resolved_no"
            resolved_outcome = "YES" if resolved_yes else "NO"

        card_outcomes.append({
            "card_id": card_id,
            "question": c.get("question") or rule["question"],
            "metric": metric_name,
            "threshold": threshold,
            "current_value": value,
            "settlement_status": settlement_status,
            "resolved_outcome": resolved_outcome,
            "resolution_deadline": c.get("resolution_deadline") or c.get("deadline"),
            "resolution_source": c.get("resolution_source") or c.get("source") or metric.get("source"),
            "resolution_note": (
                f"{metric_name}={value}, threshold={threshold}. "
                "Pending until deadline unless forced."
            ),
        })

    report = {
        "event": "short_horizon_round_settlement_dry_run",
        "round_id": ROUND_ID,
        "created_at": now_iso(),
        "mode": "finalize" if args.finalize else "dry_run",
        "status": (
            "ready_to_write_outcomes" if args.finalize and all_resolvable
            else "not_ready_pending_deadline_or_source"
        ),
        "paper_only": True,
        "virtual_credits_only": True,
        "no_real_money": True,
        "no_betting": True,
        "no_trading": True,
        "not_financial_advice": True,
        "scoring_manifest": str(SCORING_MANIFEST),
        "answers_file": str(ANSWERS_FILE),
        "agents_file": str(AGENTS_FILE),
        "outcomes_file": str(OUTCOMES_FILE),
        "now": now_iso(),
        "max_deadline": max_deadline.isoformat() if max_deadline else None,
        "before_deadline": before_deadline,
        "canonical_submission_ids": sorted(include_ids),
        "excluded_submission_ids": sorted(exclude_ids),
        "answer_rows_total": len(answer_rows),
        "answer_bad_json_lines": answer_bad_json,
        "agent_rows_total": len(agent_rows),
        "agent_bad_json_lines": agent_bad_json,
        "metrics": metrics,
        "card_outcomes": card_outcomes,
        "final_scoring_blocked_until_outcomes_resolved": True,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_json = REPORT_DIR / f"{ts}__aitestarena__short_horizon_settlement_report.json"
    report_txt = REPORT_DIR / f"{ts}__aitestarena__short_horizon_settlement_report.txt"

    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    txt_lines = [
        "AITestArena Short Horizon Settlement Report",
        f"round_id: {ROUND_ID}",
        f"mode: {report['mode']}",
        f"status: {report['status']}",
        f"now: {report['now']}",
        f"max_deadline: {report['max_deadline']}",
        f"before_deadline: {report['before_deadline']}",
        "",
        "Metrics:",
        f"- approved_unique_agents: {metrics['approved_unique_agents']['value']}",
        f"- unique_valid_forecast_agents: {metrics['unique_valid_forecast_agents']['value']}",
        f"- github_stars: {metrics['github_stars']['value']} fetch_ok={metrics['github_stars']['fetch_ok']}",
        "",
        "Card outcomes:",
    ]
    for c in card_outcomes:
        txt_lines.append(
            f"- {c['card_id']}: {c['settlement_status']} "
            f"value={c['current_value']} threshold={c['threshold']} outcome={c['resolved_outcome']}"
        )
    txt_lines += [
        "",
        "Canonical submissions:",
        *[f"- {sid}" for sid in sorted(include_ids)],
        "",
        "Excluded submissions:",
        *[f"- {sid}" for sid in sorted(exclude_ids)],
        "",
        "Safety: paper only, virtual credits only, no real money, no betting, no trading, not financial advice.",
    ]

    report_txt.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")

    if args.finalize:
        if before_deadline and not args.force_finalize:
            print(json.dumps({
                "ok": False,
                "status": "refused_before_deadline",
                "message": "Outcomes not written because deadline has not passed. Use --force-finalize only after manual decision.",
                "report_json": str(report_json),
                "report_txt": str(report_txt),
            }, ensure_ascii=False, indent=2))
            return 2

        if not all_resolvable:
            print(json.dumps({
                "ok": False,
                "status": "refused_unresolved_sources",
                "message": "Outcomes not written because at least one source is unavailable or pending.",
                "report_json": str(report_json),
                "report_txt": str(report_txt),
            }, ensure_ascii=False, indent=2))
            return 3

        outcomes = {
            "event": "short_horizon_round_outcomes_written",
            "round_id": ROUND_ID,
            "created_at": now_iso(),
            "source_report_json": str(report_json),
            "paper_only": True,
            "virtual_credits_only": True,
            "card_outcomes": card_outcomes,
        }
        OUTCOMES_FILE.write_text(json.dumps(outcomes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "round_id": ROUND_ID,
        "mode": report["mode"],
        "status": report["status"],
        "before_deadline": before_deadline,
        "max_deadline": report["max_deadline"],
        "approved_unique_agents": metrics["approved_unique_agents"]["value"],
        "unique_valid_forecast_agents": metrics["unique_valid_forecast_agents"]["value"],
        "github_stars": metrics["github_stars"]["value"],
        "github_fetch_ok": metrics["github_stars"]["fetch_ok"],
        "report_json": str(report_json),
        "report_txt": str(report_txt),
        "outcomes_written": bool(args.finalize and all_resolvable and (not before_deadline or args.force_finalize)),
        "outcomes_file": str(OUTCOMES_FILE),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
