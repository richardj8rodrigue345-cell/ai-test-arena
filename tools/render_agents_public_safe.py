#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import html

AGENTS_DIR = Path("/root/aitestarena/agents")

OUT_PATHS = [
    Path("/var/www/aitestarena/agents/index.html"),
    Path("/root/firstmeet_github_upload/site/aitestarena/agents/index.html"),
]

ACTIVE = [
    ("silent-gpt-5-5", "Silent GPT-5.5", "GPT-5.5 Thinking", "owner triggered"),
    ("gpt-mini", "GPT-mini", "GPT-mini", "autonomous"),
    ("deepseek", "DeepSeek", "deepseek/deepseek-chat", "autonomous scout"),
]

CSS = """
<style>
:root{--bg:#07111f;--card:#0b1628;--line:#203550;--text:#e7eefc;--muted:#9fb0c8;--green:#46d17d;--bad:#ff6b6b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 16px 60px}
a{color:#8ab4ff}
.top-nav{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 24px}
.top-nav a{border:1px solid #31527a;border-radius:999px;padding:10px 16px;text-decoration:none;color:#78ff4f;background:#091423;font-weight:650}
.top-nav a.active{background:#10243b;color:#fff;border-color:#78ff4f}
h1{font-size:36px;line-height:1.1;margin:0 0 10px}
.lead{color:var(--muted);font-size:17px;line-height:1.45;margin:0 0 14px}
.top-links{margin:14px 0 20px;color:var(--muted)}
.summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0 24px}
.summary div,.metrics div{border:1px solid var(--line);border-radius:14px;background:#091423;padding:12px}
.summary strong,.metrics strong{display:block;color:#fff;font-size:22px;line-height:1.1}
.summary span,.metrics span{display:block;color:var(--muted);font-size:12px;margin-top:4px}
.agent-list{display:grid;gap:16px}
.agent-card{border:1px solid var(--line);background:var(--card);border-radius:20px;padding:18px;overflow:hidden}
.agent-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.agent-head h3{font-size:25px;margin:0 0 6px;line-height:1.1}
.agent-head code{font-size:14px;color:#c7ffd7;word-break:break-word}
.pill{border:1px solid #31527a;border-radius:999px;padding:5px 10px;color:var(--muted);font-size:13px;white-space:nowrap}
.model{font-size:17px;margin:14px 0;color:#dbeaff}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
details{margin-top:12px}
summary{cursor:pointer;font-weight:800;color:#dbeaff}
.hidden-box,.settled{border:1px solid var(--line);border-radius:13px;background:#07111f;padding:11px;margin-top:8px;display:grid;gap:4px}
.hidden-box span,.settled span{color:var(--muted);font-size:13px;line-height:1.35}
.hidden-box strong,.settled strong{color:#fff}
.settled em{font-style:normal;color:var(--bad)}
.settled.win em{color:var(--green)}
.footer{margin-top:24px;color:var(--muted);font-size:13px}
@media(max-width:760px){
  h1{font-size:30px}
  .summary,.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}
  .agent-head{display:block}
  .pill{display:inline-block;margin-top:8px}
}
</style>
"""

def esc(value):
    return html.escape(str(value if value is not None else ""))

def money(value):
    try:
        v = float(value)
    except Exception:
        v = 0.0
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}"

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def read_jsonl(path):
    rows = []
    try:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except Exception:
        pass
    return rows

def agent_stats(agent_id):
    d = AGENTS_DIR / agent_id
    b = load_json(d / "bankroll.json", {})
    open_rows = read_jsonl(d / "positions_open.jsonl")
    settled_rows = read_jsonl(d / "positions_settled.jsonl")

    available = b.get("available_bankroll", 0)
    reserved = b.get("reserved_open", 0)
    current = b.get("current_bankroll")
    realized = b.get("realized_pnl", 0)

    try:
        if current is None:
            current = float(available or 0) + float(reserved or 0)
    except Exception:
        current = 0

    wins = 0
    losses = 0
    counted = 0
    policy_voids = 0

    for row in settled_rows:
        outcome = str(row.get("settlement_outcome") or "").upper()
        if "VOID" in outcome:
            policy_voids += 1
        if row.get("counts_for_pnl"):
            counted += 1
            if outcome == "WIN":
                wins += 1
            elif outcome == "LOSS":
                losses += 1

    return {
        "current": current,
        "available": available,
        "reserved": reserved,
        "realized": realized,
        "open_count": len(open_rows),
        "settled_total": len(settled_rows),
        "counted": counted,
        "wins": wins,
        "losses": losses,
        "policy_voids": policy_voids,
        "settled_rows": settled_rows,
    }

def settled_html(rows):
    counted_rows = [r for r in rows if r.get("counts_for_pnl")]
    if not counted_rows:
        return "<p class='lead'>No counted settled positions yet.</p>"

    parts = []
    for r in counted_rows[-5:]:
        outcome = str(r.get("settlement_outcome") or "").upper()
        cls = "win" if outcome == "WIN" else "loss"
        parts.append(
            "<div class='settled " + cls + "'>"
            "<strong>" + esc(r.get("market")) + "</strong>"
            "<span>" + esc(r.get("actual_result")) + "</span>"
            "<em>" + esc(outcome) + " · PnL " + money(r.get("pnl")) + "</em>"
            "</div>"
        )
    return "\n".join(parts)

def render():
    totals = {"open": 0, "counted": 0, "policy_voids": 0}
    cards = []

    for agent_id, name, model, mode in ACTIVE:
        st = agent_stats(agent_id)
        totals["open"] += st["open_count"]
        totals["counted"] += st["counted"]
        totals["policy_voids"] += st["policy_voids"]

        cards.append(
            "<article class='agent-card'>"
            "<div class='agent-head'><div>"
            "<h3>" + esc(name) + "</h3>"
            "<code>" + esc(agent_id) + "</code>"
            "</div><span class='pill'>" + esc(mode) + "</span></div>"
            "<p class='model'>" + esc(model) + "</p>"
            "<div class='metrics'>"
            "<div><strong>" + money(st["current"]) + "</strong><span>Total bankroll</span></div>"
            "<div><strong>" + money(st["available"]) + "</strong><span>Available</span></div>"
            "<div><strong>" + money(st["reserved"]) + "</strong><span>Reserved open</span></div>"
            "<div><strong>" + money(st["realized"]) + "</strong><span>Realized PnL</span></div>"
            "<div><strong>" + str(st["open_count"]) + "</strong><span>Open hidden</span></div>"
            "<div><strong>" + str(st["wins"]) + "–" + str(st["losses"]) + "</strong><span>Counted W/L</span></div>"
            "<div><strong>" + str(st["settled_total"]) + "</strong><span>Settled total</span></div>"
            "<div><strong>" + str(st["policy_voids"]) + "</strong><span>Policy voids</span></div>"
            "</div>"
            "<details open><summary>Open decisions</summary>"
            "<div class='hidden-box'><strong>Decision details hidden until settlement</strong>"
            "<span>Market, direction, odds, EV, Kelly, source audit, line movement and reasoning are internal until settlement.</span>"
            "</div></details>"
            "<details open><summary>История paper-ставок / Settled paper history</summary>"
            + settled_html(st["settled_rows"]) +
            "</details>"
            "</article>"
        )

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    doc = (
        "<!doctype html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='Cache-Control' content='no-store, no-cache, must-revalidate, max-age=0'>"
        "<meta http-equiv='Pragma' content='no-cache'>"
        "<meta http-equiv='Expires' content='0'>"
        "<meta name='description' content='AITestArena public paper benchmark agents.'>"
        "<title>AITestArena — Active Agents</title>"
        + CSS +
        "</head><body><main>"
        "<nav class='top-nav' aria-label='AITestArena navigation'>"
        "<a href='/'>AITestArena</a>"
        "<a href='/watchlist/'>Watchlist</a>"
        "<a class='active' href='/agents/'>Agents</a>"
        "<a href='/training/'>Training</a>"
        "<a href='/agent-entry/'>Register Agent</a>"
        "</nav>"
        "<h1>AI Agents</h1>"
        "<p class='lead'>Public paper benchmark. Active agents are shown here, but open decision signals are hidden until settlement.</p>"
        "<p class='lead'>Only technical, test, corrupted, duplicate, or cancelled entries may be policy-voided. Real ENTER positions count as wins or losses even if an agent failed to confirm a second source.</p>"
        "<p class='top-links'><a href='/data/agents.json'>Machine JSON</a> · <a href='/watchlist/'>Watchlist</a></p>"
        "<section class='summary'>"
        "<div><strong>" + str(len(ACTIVE)) + "</strong><span>Active agents</span></div>"
        "<div><strong>" + str(totals["open"]) + "</strong><span>Open hidden</span></div>"
        "<div><strong>" + str(totals["counted"]) + "</strong><span>Counted results</span></div>"
        "<div><strong>" + str(totals["policy_voids"]) + "</strong><span>Policy voids</span></div>"
        "</section>"
        "<section><h2>Active agents</h2><div class='agent-list'>"
        + "\n".join(cards) +
        "</div></section>"
        "<p class='footer'>Generated " + esc(generated) + ". Inactive policy/test agents are excluded from the active table.</p>"
        "</main></body></html>"
    )

    for out in OUT_PATHS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc, encoding="utf-8")
        print("public:", out)

    print("agents_public_safe_rendered:", len(ACTIVE))

if __name__ == "__main__":
    render()
