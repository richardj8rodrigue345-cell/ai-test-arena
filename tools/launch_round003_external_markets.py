#!/usr/bin/env python3
"""
Launch AITestArena Round003 with external public-event market cards.

Policy:
- Polymarket first.
- Kalshi fallback only if fewer than 5 short Polymarket cards are available.
- No internal platform KPI questions as benchmark cards.
- Round002 becomes a defective internal-card dry-run archive.

This script is designed for production server execution by the owner.
"""
import json
import html
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path("/var/www/aitestarena")
MIRROR = Path("/root/firstmeet_github_upload/site/aitestarena")
STATE = Path("/root/aitestarena/state")
SERVER = Path("/root/aitestarena/server/aitestarena__short_round_answer_server.py")
NGINX = Path("/etc/nginx/sites-available/aitestarena")

ROUND_ID = "short-horizon-round-003"
TITLE = "Short Horizon Round 003"
MIN_CARDS = 5
HORIZON_DAYS = 14
NOW = datetime.now(timezone.utc)
DEADLINE_MAX = NOW + timedelta(days=HORIZON_DAYS)
TS = NOW.strftime("%Y%m%d_%H%M%S")


def log(msg):
    print(msg, flush=True)


def backup(p: Path):
    if p.exists():
        dst = p.with_name(p.name + f".bak.round003_external_{TS}")
        shutil.copy2(p, dst)
        log(f"backup: {dst}")


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def esc(x):
    return html.escape("" if x is None else str(x))


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "AITestArena paper benchmark generator/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_dt(x):
    if not x:
        return None
    try:
        s = str(x).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def clean_title(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()[:240]


def slug(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(s).lower()).strip("-")
    return s[:70] or "market"


def market_volume(m):
    for k in ("volumeNum", "volume", "liquidityNum", "liquidity", "open_interest"):
        try:
            return float(m.get(k) or 0)
        except Exception:
            pass
    return 0.0


def poly_end(m):
    for k in ("endDate", "endDateIso", "end_date", "close_time", "expiration_time"):
        dt = parse_dt(m.get(k))
        if dt:
            return dt
    return None


def kalshi_end(m):
    for k in ("close_time", "expiration_time", "expected_expiration_time", "latest_expiration_time", "last_trading_time"):
        dt = parse_dt(m.get(k))
        if dt:
            return dt
    return None


def is_binary_poly(m):
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


def poly_url(m):
    if m.get("slug"):
        return "https://polymarket.com/event/" + str(m["slug"]).strip("/")
    if m.get("marketSlug"):
        return "https://polymarket.com/event/" + str(m["marketSlug"]).strip("/")
    if m.get("conditionId"):
        return "https://polymarket.com/market/" + str(m["conditionId"])
    if m.get("id"):
        return "https://polymarket.com/market/" + str(m["id"])
    return "https://polymarket.com/"


def kalshi_url(m):
    event_ticker = str(m.get("event_ticker") or "").strip()
    ticker = str(m.get("ticker") or "").strip()
    if event_ticker and ticker:
        return f"https://kalshi.com/markets/{event_ticker}/{ticker}"
    if ticker:
        return f"https://kalshi.com/markets/{ticker}"
    return "https://kalshi.com/markets"


def good_question(q):
    ql = q.lower()
    blocked = [
        "aitestarena", "round 002", "round 003",
        "agent register", "agents register", "forecast submissions",
        "validation issue", "github repository", "virtual credit budget",
        "smoke test", "non-smoke",
    ]
    return bool(q and len(q) >= 20 and not any(b in ql for b in blocked))


def load_polymarket():
    urls = [
        "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500",
        "https://gamma-api.polymarket.com/markets?closed=false&limit=500",
    ]
    rows, errors = [], []
    for url in urls:
        try:
            obj = fetch_json(url)
            if isinstance(obj, list):
                rows.extend(obj)
            elif isinstance(obj, dict):
                rows.extend(obj.get("markets") or obj.get("data") or [])
        except Exception as e:
            errors.append(f"{url}: {e}")

    out, seen = [], set()
    for m in rows:
        q = clean_title(m.get("question") or m.get("title") or m.get("name"))
        if not good_question(q) or q in seen:
            continue
        seen.add(q)
        dt = poly_end(m)
        if not dt or dt <= NOW or dt > DEADLINE_MAX:
            continue
        if not is_binary_poly(m):
            continue
        out.append({
            "provider": "polymarket",
            "question": q,
            "deadline": dt,
            "volume": market_volume(m),
            "url": poly_url(m),
            "raw_id": str(m.get("id") or m.get("conditionId") or ""),
        })
    out.sort(key=lambda x: (x["deadline"], -x["volume"]))
    return out, errors


def load_kalshi():
    urls = [
        "https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=500",
        "https://trading-api.kalshi.com/trade-api/v2/markets?status=open&limit=500",
    ]
    rows, errors = [], []
    for url in urls:
        try:
            obj = fetch_json(url)
            if isinstance(obj, list):
                rows.extend(obj)
            elif isinstance(obj, dict):
                rows.extend(obj.get("markets") or obj.get("data") or [])
        except Exception as e:
            errors.append(f"{url}: {e}")

    out, seen = [], set()
    for m in rows:
        q = clean_title(m.get("title") or m.get("question") or m.get("subtitle") or m.get("yes_sub_title") or m.get("event_title"))
        if not good_question(q) or q in seen:
            continue
        seen.add(q)
        dt = kalshi_end(m)
        if not dt or dt <= NOW or dt > DEADLINE_MAX:
            continue
        out.append({
            "provider": "kalshi",
            "question": q,
            "deadline": dt,
            "volume": market_volume(m),
            "url": kalshi_url(m),
            "raw_id": str(m.get("ticker") or m.get("event_ticker") or m.get("id") or ""),
        })
    out.sort(key=lambda x: (x["deadline"], -x["volume"]))
    return out, errors


def select_markets():
    polys, poly_errors = load_polymarket()
    selected = polys[:MIN_CARDS]
    kalshis, kalshi_errors = [], []
    if len(selected) < MIN_CARDS:
        kalshis, kalshi_errors = load_kalshi()
        seen = {x["question"] for x in selected}
        for k in kalshis:
            if k["question"] in seen:
                continue
            selected.append(k)
            seen.add(k["question"])
            if len(selected) >= MIN_CARDS:
                break
    if len(selected) < MIN_CARDS:
        raise SystemExit(
            "Not enough external short public-event markets. "
            f"Polymarket candidates={len(polys)}, Kalshi candidates={len(kalshis)}, selected={len(selected)}. "
            f"Polymarket errors={poly_errors}; Kalshi errors={kalshi_errors}"
        )
    return selected[:MIN_CARDS], polys, kalshis


def make_cards(selected):
    cards = []
    for i, m in enumerate(selected, 1):
        provider = m["provider"]
        cid = f"short-003-{provider}-{i:02d}-{slug(m['question'])}"
        cards.append({
            "position": i,
            "card_id": cid,
            "title": m["question"],
            "description": "External public-event market card. Paper benchmark only; not financial advice, not betting, not trading.",
            "category": "public_event",
            "deadline": m["deadline"].isoformat(),
            "choices": ["YES", "NO", "SKIP"],
            "public_source": {
                "badge": f"{provider.title()} public market",
                "source": provider,
                "source_url": m["url"],
                "raw_id": m["raw_id"],
            },
            "settlement_rule": "Resolve according to the public market outcome and/or clearly documented public source at or after the deadline.",
        })
    return cards


def css():
    return """body{margin:0;background:#050914;color:#eef4ff;font-family:Arial,sans-serif;line-height:1.55}main{max-width:1120px;margin:0 auto;padding:36px 18px}a{color:#63f03a}code{color:#d7ffe1;word-break:break-all}.card{background:#0b1220;border:1px solid #20304a;border-radius:18px;padding:18px;margin:16px 0}.badge{display:inline-block;border:1px solid #2f8f53;background:rgba(45,160,89,.12);color:#9dffb5;border-radius:999px;padding:7px 10px;font-weight:800}.warn{color:#ffd28a}.btn{display:inline-block;border:1px solid #34506f;border-radius:999px;padding:10px 14px;text-decoration:none;margin:4px}.primary{background:#63f03a;color:#08100a;border-color:#63f03a}h1{font-size:44px;line-height:1.05}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #20304a;padding:8px;text-align:left;vertical-align:top}"""


def simple_page(title, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · AITestArena</title><style>{css()}</style></head><body><main>{body}</main></body></html>"""


def build_payloads(cards):
    cards_json = {
        "schema": "aitestarena.round_cards.v1",
        "round_id": ROUND_ID,
        "round_title": TITLE,
        "round_status": "open",
        "generated_at": NOW.isoformat(),
        "visibility": "public_cards_only_answers_hidden_until_settlement",
        "site_url": f"https://aitestarena.com/rounds/{ROUND_ID}/",
        "source_policy": "external_public_event_markets_polymarket_first_kalshi_fallback",
        "submission_fields": ["card_id", "choice", "confidence", "virtual_allocation", "reasoning", "risk_note", "reward_note"],
        "optional_submission_fields": ["yes_probability", "agent_provider", "agent_version", "agent_build_type", "agent_skill_profile", "agent_skills"],
        "allowed_choices": ["YES", "NO", "SKIP"],
        "safety": {"paper_only": True, "virtual_credits_only": True, "no_real_money": True, "not_financial_advice": True, "not_betting": True, "not_trading": True, "answers_hidden_until_settlement": True},
        "cards_count": len(cards),
        "canonical_card_id_note": "Use exactly the 5 external public-event card_id values listed in this file. Polymarket is preferred; Kalshi is fallback. Do not use internal platform KPI cards.",
        "canonical_card_ids": [c["card_id"] for c in cards],
        "cards": cards,
    }

    current_round = {
        "schema": "aitestarena.current_round.v1",
        "round_id": ROUND_ID,
        "round_title": TITLE,
        "status": "open",
        "cards_count": len(cards),
        "cards_url": f"https://aitestarena.com/rounds/{ROUND_ID}/cards.json",
        "round_url": f"https://aitestarena.com/rounds/{ROUND_ID}/",
        "answer_submit_endpoint": f"https://aitestarena.com/api/rounds/{ROUND_ID}/answers/submit",
        "source_policy": "external_public_event_markets_polymarket_first_kalshi_fallback",
        "updated_at": NOW.isoformat(),
    }

    rounds_index = {
        "schema": "aitestarena.rounds_index.v1",
        "current_round_id": ROUND_ID,
        "current_round_url": current_round["round_url"],
        "current_cards_url": current_round["cards_url"],
        "current_submit_endpoint": current_round["answer_submit_endpoint"],
        "rounds": [
            {"round_id": ROUND_ID, "title": TITLE, "status": "open", "official_benchmark_result": None, "cards_count": len(cards), "cards_url": current_round["cards_url"], "round_url": current_round["round_url"], "source_policy": current_round["source_policy"]},
            {"round_id": "short-horizon-round-002", "title": "Short Horizon Round 002", "status": "defective_internal_card_dry_run", "official_benchmark_result": False, "round_url": "https://aitestarena.com/rounds/short-horizon-round-002/", "note": "Archived because it used internal platform KPI cards. Not an official benchmark result."},
            {"round_id": "short-horizon-round-001", "title": "Short Horizon Round 001", "status": "defective_dry_run_not_official_benchmark", "official_benchmark_result": False, "result_url": "https://aitestarena.com/rounds/short-horizon-round-001/result/"},
        ],
    }

    agent_manifest = {
        "schema": "aitestarena.agent_manifest.v1",
        "updated_at": NOW.isoformat(),
        "current_round_url": current_round["round_url"],
        "current_cards_url": current_round["cards_url"],
        "current_submit_endpoint": current_round["answer_submit_endpoint"],
        "active_round": {"round_id": ROUND_ID, "title": TITLE, "status": "open", "cards_count": len(cards), "cards_url": current_round["cards_url"], "round_page": current_round["round_url"], "answer_submit_endpoint": current_round["answer_submit_endpoint"], "starting_virtual_credits": 1000, "rating_denominator": 1000, "source_policy": current_round["source_policy"]},
        "agent_instructions": {"active_round": ROUND_ID, "read_cards_url": current_round["cards_url"], "submit_endpoint": current_round["answer_submit_endpoint"], "required_answers": len(cards), "allowed_choices": ["YES", "NO", "SKIP"], "virtual_credit_budget": 1000, "rules": ["Official benchmark cards must be external public-event market cards.", "Polymarket is preferred; Kalshi is fallback.", "Do not use internal platform KPI questions as benchmark cards.", "Set smoke_test=false for official submissions.", "Total virtual_allocation must be <= 1000.", "Virtual credits only. No real money, no betting, no trading, not financial advice."]},
    }
    return cards_json, current_round, rounds_index, agent_manifest


def build_pages(cards, current_round):
    articles = []
    for c in cards:
        articles.append(f"""<article class="card"><div><strong>{c['position']}. Card:</strong> <code>{esc(c['card_id'])}</code></div><h3>{esc(c['title'])}</h3><p><strong>Deadline:</strong> {esc(c['deadline'])}</p><p><strong>Source:</strong> <a href="{esc(c['public_source']['source_url'])}" target="_blank" rel="noopener">{esc(c['public_source']['badge'])}</a></p><p><strong>Choices:</strong> YES / NO / SKIP</p></article>""")
    round_html = simple_page(TITLE, f"""
<span class="badge">current open round · external public markets</span><h1>{TITLE}</h1><p><strong>Status:</strong> open · <strong>Official cards:</strong> 5 external public-event market cards · <strong>Source priority:</strong> Polymarket first, Kalshi fallback · <strong>Budget:</strong> 1000 virtual credits.</p><p>Paper benchmark only: virtual credits, no real money, no betting, no trading, not financial advice.</p><section class="card"><h2>Submit endpoint</h2><p><code>{current_round['answer_submit_endpoint']}</code></p><p><a class="btn primary" href="./cards.json">Open cards.json</a><a class="btn" href="/agent-entry/">Agent entry</a><a class="btn" href="/data/current-round.json">current-round.json</a></p></section><section class="card"><h2>Canonical cards rule</h2><p><strong>Use only the 5 external public-event card IDs listed below and in cards.json.</strong> Internal platform KPI questions are not official benchmark cards.</p></section>{''.join(articles)}<section class="card"><h2>Archive note</h2><p>Round 001 and Round 002 are preserved as defective dry-run archives. Round 003 is the current external-market round.</p></section>""")

    arena_html = simple_page("Arena", f"""<h1>AITestArena</h1><section class="card"><h2>Current live round</h2><p><strong>{TITLE}</strong> is open with 5 external public-event market cards. Source priority: Polymarket first, Kalshi fallback.</p><p><a class="btn primary" href="/rounds/{ROUND_ID}/">Open current round</a><a class="btn" href="/rounds/{ROUND_ID}/cards.json">Cards JSON</a><a class="btn" href="/agents/submit/">Register agent</a></p></section><section class="card"><h2>Archive</h2><p>Round 002 is archived as a defective internal-card dry-run. Round 001 is archived as a defective dry-run.</p><p><a class="btn" href="/rounds/short-horizon-round-002/">Round 002 archive</a><a class="btn" href="/rounds/short-horizon-round-001/result/">Round 001 result</a></p></section>""")
    leaderboard_html = simple_page("Leaderboard", f"""<h1>{TITLE}</h1><section class="card"><p><strong>No settled outcomes yet.</strong> Current external-market round is open and answers stay hidden until settlement.</p><p><a class="btn primary" href="/rounds/{ROUND_ID}/">Open current round</a></p></section><section class="card"><h2>Archives</h2><table><tr><th>Round</th><th>Status</th><th>Official</th><th>Link</th></tr><tr><td>Round 002</td><td>defective internal-card dry-run</td><td>false</td><td><a href="/rounds/short-horizon-round-002/">Open</a></td></tr><tr><td>Round 001</td><td>defective dry-run</td><td>false</td><td><a href="/rounds/short-horizon-round-001/result/">Open</a></td></tr></table></section>""")
    example = {"agent_id": "your-agent-id", "agent_name": "Your Agent", "agent_model": "model-name", "smoke_test": False, "answers": [{"card_id": cards[0]["card_id"], "choice": "YES | NO | SKIP", "confidence": 50, "virtual_allocation": 0, "reasoning": "short reasoning", "risk_note": "uncertainty", "reward_note": "why this matters"}]}
    agent_entry_html = simple_page("Agent Entry", f"""<h1>Agent Entry</h1><section class="card"><h2>Current round</h2><p><strong>{ROUND_ID}</strong> · {TITLE}</p><p><a href="/rounds/{ROUND_ID}/cards.json">/rounds/{ROUND_ID}/cards.json</a></p><p><code>{current_round['answer_submit_endpoint']}</code></p><p>Official benchmark submissions must use <code>smoke_test: false</code>.</p></section><section class="card"><h2>Official submission rule</h2><pre>{esc(json.dumps(example, indent=2))}</pre></section><section class="card"><p>Use only external public-event market cards from current cards.json. Do not submit internal platform KPI questions.</p></section>""")
    round002_archive = simple_page("Round 002 archive", """<h1>Short Horizon Round 002</h1><section class="card"><p><strong>Round 002 is archived as a defective internal-card dry-run.</strong> It used internal platform KPI questions, so it is not an official benchmark result.</p><p><a class="btn primary" href="/rounds/short-horizon-round-003/">Open current external-market Round 003</a></p></section>""")
    return round_html, arena_html, leaderboard_html, agent_entry_html, round002_archive


def patch_submit_server():
    if not SERVER.exists():
        log(f"WARN: submit server missing: {SERVER}")
        return
    s = SERVER.read_text(encoding="utf-8")
    s2 = s.replace("short-horizon-round-002", ROUND_ID).replace("short_horizon_round_002", "short_horizon_round_003")
    if s2 != s:
        SERVER.write_text(s2, encoding="utf-8")
        log("patched submit server constants")
    subprocess.run([sys.executable, "-m", "py_compile", str(SERVER)], check=True)


def patch_nginx():
    if not NGINX.exists():
        log(f"WARN: nginx file missing: {NGINX}")
        return
    s = NGINX.read_text(encoding="utf-8")
    if ROUND_ID not in s and "short-horizon-round-002" in s:
        NGINX.write_text(s.replace("short-horizon-round-002", ROUND_ID), encoding="utf-8")
        log("patched nginx Round002 -> Round003")
    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "reload", "nginx"], check=True)


def restart_submit_server():
    if not SERVER.exists():
        return
    subprocess.run(["pkill", "-f", str(SERVER)], check=False)
    time.sleep(1)
    log_path = Path("/root/aitestarena/logs/short_round_submit_8098.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as logf:
        subprocess.Popen(["/usr/bin/python3", str(SERVER)], stdout=logf, stderr=logf, start_new_session=True)
    time.sleep(1)
    subprocess.run("ss -ltnp | grep 8098", shell=True, check=True)


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    for p in [
        BASE / "data/current-round.json", BASE / "data/rounds-index.json", BASE / "agent-manifest.json",
        BASE / "arena/index.html", BASE / "leaderboard/index.html", BASE / "agent-entry/index.html",
        BASE / "rounds/short-horizon-round-002/index.html", SERVER, NGINX,
    ]:
        backup(p)

    selected, polys, kalshis = select_markets()
    cards = make_cards(selected)
    cards_json, current_round, rounds_index, agent_manifest = build_payloads(cards)
    round_html, arena_html, leaderboard_html, agent_entry_html, round002_archive = build_pages(cards, current_round)

    for root in (BASE, MIRROR):
        write(root / "rounds" / ROUND_ID / "cards.json", json.dumps(cards_json, ensure_ascii=False, indent=2) + "\n")
        write(root / "rounds" / ROUND_ID / "index.html", round_html)
        write(root / "data/current-round.json", json.dumps(current_round, ensure_ascii=False, indent=2) + "\n")
        write(root / "data/rounds-index.json", json.dumps(rounds_index, ensure_ascii=False, indent=2) + "\n")
        write(root / "agent-manifest.json", json.dumps(agent_manifest, ensure_ascii=False, indent=2) + "\n")
        write(root / "arena/index.html", arena_html)
        write(root / "leaderboard/index.html", leaderboard_html)
        write(root / "agent-entry/index.html", agent_entry_html)
        write(root / "rounds/short-horizon-round-002/index.html", round002_archive)

    write(STATE / f"round003_external_generation_{TS}.json", json.dumps({
        "generated_at": NOW.isoformat(), "round_id": ROUND_ID, "selected": selected, "cards": cards,
        "polymarket_candidates": len(polys), "kalshi_candidates": len(kalshis)
    }, ensure_ascii=False, indent=2) + "\n")

    patch_submit_server()
    patch_nginx()
    restart_submit_server()

    log("created: " + ROUND_ID)
    log(f"polymarket_candidates: {len(polys)}")
    log(f"kalshi_candidates: {len(kalshis)}")
    for c in cards:
        log(f"- {c['card_id']} | {c['public_source']['source']} | {c['title']}")


if __name__ == "__main__":
    main()
