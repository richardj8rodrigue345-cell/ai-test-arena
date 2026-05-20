#!/usr/bin/env python3
"""
Generate AITestArena Round003 hybrid candidate cards without opening the round.

This script only writes candidate artifacts. It does NOT touch:
- current-round.json
- rounds-index.json
- agent-manifest.json
- submit server
- nginx

Default mix:
- 3 external_market cards, preferably Polymarket
- 2 platform_meta cards

Human/DeepSeek approval is required before promotion to open.
"""
import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROUND_ID = "short-horizon-round-003"
ROUND_TITLE = "Short Horizon Round 003"
DEFAULT_OUT_DIRS = [
    Path("/var/www/aitestarena/rounds/short-horizon-round-003"),
    Path("/root/firstmeet_github_upload/site/aitestarena/rounds/short-horizon-round-003"),
]


def fetch_json(url: str, timeout: int = 25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AITestArena hybrid candidate generator/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str, max_len: int = 72) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:max_len] or "card"


def looks_bad_question(title: str) -> bool:
    q = clean_text(title)
    ql = q.lower()
    if len(q) < 28:
        return True
    if ql.startswith(("yes ", "no ", "yes$", "no$", "yes $", "no $")):
        return True
    if ql.count("yes ") + ql.count("no ") >= 2:
        return True
    if re.search(r"^(yes|no)\s*\$?\d", ql):
        return True
    blocked = [
        "aitestarena",
        "round 002",
        "round 003",
        "agent register",
        "agents register",
        "forecast submission",
        "validation issue",
        "github repository",
        "virtual credit budget",
        "smoke test",
        "non-smoke",
    ]
    return any(b in ql for b in blocked)


def market_volume(m: dict) -> float:
    for key in ("volumeNum", "volume", "liquidityNum", "liquidity", "open_interest"):
        try:
            return float(m.get(key) or 0)
        except Exception:
            pass
    return 0.0


def polymarket_deadline(m: dict):
    for key in ("endDate", "endDateIso", "end_date", "close_time", "expiration_time"):
        dt = parse_dt(m.get(key))
        if dt:
            return dt
    return None


def polymarket_url(m: dict) -> str:
    if m.get("slug"):
        return "https://polymarket.com/event/" + str(m["slug"]).strip("/")
    if m.get("marketSlug"):
        return "https://polymarket.com/event/" + str(m["marketSlug"]).strip("/")
    if m.get("conditionId"):
        return "https://polymarket.com/market/" + str(m["conditionId"])
    if m.get("id"):
        return "https://polymarket.com/market/" + str(m["id"])
    return "https://polymarket.com/"


def is_binary_polymarket(m: dict) -> bool:
    outcomes = m.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except Exception:
            outcomes = []
    if isinstance(outcomes, list) and outcomes:
        vals = {str(x).strip().upper() for x in outcomes}
        return "YES" in vals and "NO" in vals
    return True


def load_polymarket_candidates(now: datetime, deadline_max: datetime):
    urls = [
        "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500",
        "https://gamma-api.polymarket.com/markets?closed=false&limit=500",
    ]
    rows = []
    errors = []
    for url in urls:
        try:
            obj = fetch_json(url)
            if isinstance(obj, list):
                rows.extend(obj)
            elif isinstance(obj, dict):
                rows.extend(obj.get("markets") or obj.get("data") or [])
        except Exception as exc:
            errors.append({"url": url, "error": repr(exc)})

    out = []
    seen = set()
    rejected = []
    for m in rows:
        title = clean_text(m.get("question") or m.get("title") or m.get("name"))
        if not title or title in seen:
            continue
        seen.add(title)
        dt = polymarket_deadline(m)
        source_url = polymarket_url(m)
        if looks_bad_question(title):
            rejected.append({"title": title, "source_url": source_url, "reason": "not human-readable or blocked wording"})
            continue
        if not dt or dt <= now or dt > deadline_max:
            rejected.append({"title": title, "source_url": source_url, "reason": "deadline missing/outside horizon"})
            continue
        if not is_binary_polymarket(m):
            rejected.append({"title": title, "source_url": source_url, "reason": "not binary YES/NO"})
            continue
        out.append(
            {
                "provider": "polymarket",
                "title": title,
                "deadline": dt,
                "source_url": source_url,
                "raw_id": str(m.get("id") or m.get("conditionId") or ""),
                "volume": market_volume(m),
            }
        )
    out.sort(key=lambda x: (x["deadline"], -x["volume"]))
    return out, rejected[:50], errors


def make_external_card(position: int, candidate: dict):
    card_id = f"short-003-ext-{position:02d}-{slugify(candidate['title'])}"
    return {
        "position": position,
        "track": "external_market",
        "card_id_suggestion": card_id,
        "title": candidate["title"],
        "source": candidate["provider"],
        "source_url": candidate["source_url"],
        "deadline_utc": candidate["deadline"].isoformat(),
        "yes_rule": "YES if the linked public market resolves YES before or at settlement according to the public market/source outcome.",
        "no_rule": "NO if the linked public market resolves NO or does not meet the YES condition by settlement.",
        "public_verification": "Verify through the linked public market page and archived settlement note.",
        "why_interesting": "External public-event calibration card for comparing AI forecasts against a market outcome.",
        "quality_notes": [],
    }


def platform_meta_cards(start_position: int, deadline: datetime):
    deadline_iso = deadline.isoformat()
    return [
        {
            "position": start_position,
            "track": "platform_meta",
            "card_id_suggestion": "short-003-meta-01-three-valid-agent-submissions",
            "title": "Will at least 3 unique AI agents submit valid Round 003 forecasts before the deadline?",
            "source": "aitestarena_public_status",
            "source_url": "https://aitestarena.com/leaderboard/",
            "deadline_utc": deadline_iso,
            "yes_rule": "YES if at least 3 unique non-smoke agent_ids have accepted, valid Round 003 forecast submissions before the deadline.",
            "no_rule": "NO if fewer than 3 unique non-smoke agent_ids have accepted, valid Round 003 forecast submissions before the deadline.",
            "public_verification": "Verify through the public Round 003 final status/leaderboard or settlement report published by AITestArena.",
            "why_interesting": "Measures whether the round attracted enough real agent participation to be a useful benchmark, not just a static demo.",
            "quality_notes": ["platform_meta card; not an external market card", "smoke tests excluded"],
        },
        {
            "position": start_position + 1,
            "track": "platform_meta",
            "card_id_suggestion": "short-003-meta-02-one-external-agent-submission",
            "title": "Will at least 1 non-owner external AI agent submit a valid Round 003 forecast before the deadline?",
            "source": "aitestarena_public_status",
            "source_url": "https://aitestarena.com/arena/",
            "deadline_utc": deadline_iso,
            "yes_rule": "YES if at least one accepted non-smoke Round 003 forecast is submitted by an agent that is not controlled by the site owner/operator before the deadline.",
            "no_rule": "NO if no non-owner external AI agent submits an accepted non-smoke Round 003 forecast before the deadline.",
            "public_verification": "Verify through the public Round 003 final status/leaderboard or settlement report published by AITestArena.",
            "why_interesting": "Separates real third-party interest from owner-operated/demo-agent activity.",
            "quality_notes": ["platform_meta card; owner/demo agents must be excluded", "requires settlement report to label owner/demo agents"],
        },
    ]


def candidate_pack(round_deadline_days: int):
    now = datetime.now(timezone.utc)
    deadline_max = now + timedelta(days=round_deadline_days)
    external, rejected, errors = load_polymarket_candidates(now, deadline_max)
    selected_external = external[:3]
    # Round deadline should cover all external cards and meta cards.
    if selected_external:
        deadline = max([x["deadline"] for x in selected_external] + [now + timedelta(days=3)])
    else:
        deadline = now + timedelta(days=3)

    cards = []
    for i, item in enumerate(selected_external, start=1):
        cards.append(make_external_card(i, item))
    cards.extend(platform_meta_cards(len(cards) + 1, deadline))

    status = "OK" if len(selected_external) == 3 else "WARN"
    summary = "Hybrid candidate generated: 3 external_market + 2 platform_meta." if status == "OK" else f"Only {len(selected_external)} quality external cards found; candidate needs review or broader source search."
    quality = {
        "no_internal_kpi_confusion": True,
        "no_machine_fragments": all(not looks_bad_question(c["title"]) for c in cards),
        "all_sources_public_or_documented": all(bool(c.get("source_url")) for c in cards),
        "all_titles_human_readable": all(not looks_bad_question(c["title"]) for c in cards),
        "tracks_clearly_labeled": all(c.get("track") in {"external_market", "platform_meta"} for c in cards),
        "external_cards_found": len(selected_external),
        "external_cards_required": 3,
    }

    return {
        "schema": "aitestarena.round_candidate_pack.v1",
        "audit_id": "candidate-pack-" + now.strftime("%Y%m%d-%H%M%S"),
        "status": status,
        "summary": summary,
        "generated_at": now.isoformat(),
        "round_candidate": {
            "round_id_suggestion": ROUND_ID,
            "round_title": ROUND_TITLE,
            "status": "candidate_pending_review",
            "recommended_deadline_utc": deadline.isoformat(),
            "cards_count": len(cards),
            "mix": {"external_market": len(selected_external), "platform_meta": 2},
            "cards": cards,
        },
        "rejected_candidates": rejected[:25],
        "source_errors": errors,
        "quality_check": quality,
        "safe_to_promote_to_open": False,
        "requires_human_approval": True,
        "next_actions": [
            "Ask DeepSeek to audit candidate_cards.json for clarity/source quality.",
            "Owner approves or rejects the 5-card candidate pack.",
            "Only after approval, promote to current/open round and enable official submissions.",
        ],
    }


def write_pack(pack: dict, out_dirs):
    for d in out_dirs:
        d.mkdir(parents=True, exist_ok=True)
        (d / "candidate_cards.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "candidate_cards.html").write_text(render_html(pack), encoding="utf-8")


def render_html(pack: dict) -> str:
    cards = pack["round_candidate"]["cards"]
    rows = []
    for c in cards:
        rows.append(
            f"<article class='card'><div><strong>{c['position']}. {c['track']}</strong></div>"
            f"<h2>{escape(c['title'])}</h2>"
            f"<p><strong>Source:</strong> <a href='{escape(c['source_url'])}'>{escape(c['source'])}</a></p>"
            f"<p><strong>Deadline:</strong> {escape(c['deadline_utc'])}</p>"
            f"<p><strong>YES:</strong> {escape(c['yes_rule'])}</p>"
            f"<p><strong>NO:</strong> {escape(c['no_rule'])}</p>"
            f"<p><strong>Why interesting:</strong> {escape(c['why_interesting'])}</p></article>"
        )
    return """<!doctype html><html><head><meta charset='utf-8'><title>Round003 candidate cards</title><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{margin:0;background:#050914;color:#eef4ff;font-family:Arial,sans-serif;line-height:1.55}main{max-width:1050px;margin:0 auto;padding:36px 18px}a{color:#63f03a}.card{background:#0b1220;border:1px solid #20304a;border-radius:18px;padding:18px;margin:16px 0}.badge{display:inline-block;border:1px solid #6b4a21;background:#2a1c10;color:#ffd28a;border-radius:999px;padding:7px 10px;font-weight:800}</style></head><body><main>""" + f"<span class='badge'>candidate pending review</span><h1>{escape(pack['round_candidate']['round_title'])}</h1><p>{escape(pack['summary'])}</p><p><strong>Status:</strong> {escape(pack['status'])} · <strong>safe_to_promote_to_open:</strong> false</p>" + "".join(rows) + "</main></body></html>"


def escape(x):
    return str(x or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline-days", type=int, default=30, help="External-market candidate horizon in days")
    parser.add_argument("--out-dir", action="append", help="Output directory. Defaults to public + mirror Round003 dirs.")
    args = parser.parse_args()
    out_dirs = [Path(x) for x in args.out_dir] if args.out_dir else DEFAULT_OUT_DIRS
    pack = candidate_pack(args.deadline_days)
    write_pack(pack, out_dirs)
    print(json.dumps({
        "status": pack["status"],
        "summary": pack["summary"],
        "cards_count": pack["round_candidate"]["cards_count"],
        "mix": pack["round_candidate"]["mix"],
        "candidate_json": [str(d / "candidate_cards.json") for d in out_dirs],
        "candidate_html": [str(d / "candidate_cards.html") for d in out_dirs],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
