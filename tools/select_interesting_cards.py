#!/usr/bin/env python3
"""
AITestArena Mini Arena Scout prefilter.

Purpose:
- local deterministic filter;
- no OpenAI/model calls;
- select only top 1-3 interesting forecast cards;
- reduce GPT-5.5 cost by avoiding full card-list analysis.

Safe mode:
- reads candidate JSON/JSONL files;
- reads existing gpt-mini history to avoid duplicates;
- writes only one preview JSON: /root/aitestarena/state/mini_scout_prefilter_latest.json
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path("/root/aitestarena")
STATE = ROOT / "state"
OUT_DEFAULT = STATE / "mini_scout_prefilter_latest.json"

AGENT_IDS = {"gpt-mini", "northstar-2fc6285f", "mini", "Mini Arena Scout"}

VAGUE_PATTERNS = [
    r"\bwill this\b",
    r"\bbe good\b",
    r"\binteresting\b",
    r"\bsuccessful\b",
    r"\bpopular\b",
    r"\bviral\b",
    r"\bfeel\b",
    r"\bshould\b",
    r"хорош",
    r"успешн",
    r"популяр",
    r"интересн",
]

INTERNAL_PATTERNS = [
    r"agent registrations",
    r"aitestarena register",
    r"firstmeet receive",
    r"project growth",
    r"internal",
    r"platform",
    r"directory_submissions",
]

SOURCE_HINTS = [
    ROOT / "state",
    ROOT / "rounds",
    ROOT / "data",
    ROOT / "watchlist" / "active",
    Path("/var/www/aitestarena/data"),
    Path("/var/www/aitestarena/rounds"),
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any):
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def read_json_any(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return None
    if not text:
        return None

    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
        return rows

    try:
        return json.loads(text)
    except Exception:
        return None


def walk_dicts(obj: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from walk_dicts(x)


def card_id(card: Dict[str, Any]) -> str:
    for k in ("card_id", "event_id", "id", "question_id", "slug"):
        v = card.get(k)
        if v:
            return str(v).strip()
    title = card.get("title") or card.get("question") or card.get("event")
    if title:
        return re.sub(r"[^a-zA-Z0-9]+", "-", str(title).strip().lower())[:120]
    return ""


def title_of(card: Dict[str, Any]) -> str:
    return str(card.get("title") or card.get("question") or card.get("event") or "").strip()


def resolution_of(card: Dict[str, Any]) -> str:
    return str(
        card.get("resolution_condition")
        or card.get("settlement_rule")
        or card.get("resolve_rule")
        or card.get("condition")
        or ""
    ).strip()


def deadline_of(card: Dict[str, Any]):
    for k in ("deadline", "resolution_deadline", "end_time", "start_time_utc", "deadline_utc"):
        dt = parse_dt(card.get(k))
        if dt:
            return dt
    return None


def market_prob(card: Dict[str, Any]):
    for k in ("market_probability_yes", "probability_yes", "baseline_probability_yes", "market_prob_yes"):
        v = card.get(k)
        if v is None or v == "":
            continue
        try:
            x = float(v)
            if 0 <= x <= 1:
                return round(x * 100)
            if 0 <= x <= 100:
                return round(x)
        except Exception:
            pass
    return None


def is_resolved(card: Dict[str, Any]) -> bool:
    status = str(card.get("status") or card.get("settlement_status") or "").lower()
    if status in {"resolved", "settled", "closed", "final"}:
        return True
    if card.get("resolved_at") or card.get("resolved_outcome") or card.get("settlement_outcome"):
        return True
    return False


def is_yes_no(card: Dict[str, Any]) -> bool:
    text = " ".join([title_of(card), resolution_of(card)]).lower()
    if "yes" in text or "no" in text:
        return True
    choices = card.get("choices") or card.get("options")
    if isinstance(choices, list):
        vals = {str(x).strip().lower() for x in choices}
        if {"yes", "no"}.issubset(vals):
            return True
    return False


def load_seen_event_ids() -> set:
    seen = set()
    paths = [
        ROOT / "agents/gpt-mini/decisions.jsonl",
        ROOT / "agents/gpt-mini/positions_open.jsonl",
        ROOT / "agents/gpt-mini/positions_settled.jsonl",
        ROOT / "state/aitestarena__rounds__short_horizon_round_001__agent_answers.jsonl",
    ]
    for p in paths:
        data = read_json_any(p)
        if not data:
            continue
        for row in walk_dicts(data):
            aid = str(row.get("agent_id") or row.get("linked_agent_id") or "").strip()
            if aid and aid not in AGENT_IDS and aid != "gpt-mini":
                continue
            for k in ("event_id", "card_id", "question_id"):
                if row.get(k):
                    seen.add(str(row[k]).strip())
            answers = row.get("answers")
            if isinstance(answers, list):
                for a in answers:
                    if isinstance(a, dict):
                        for k in ("event_id", "card_id", "question_id"):
                            if a.get(k):
                                seen.add(str(a[k]).strip())
    return seen


def likely_source_files() -> List[Path]:
    out = []

    # Critical: active watchlist files often have hash filenames, so include all JSON/JSONL there.
    watch_root = ROOT / "watchlist" / "active"
    if watch_root.exists():
        for p in watch_root.glob("*.json"):
            out.append(p)
        for p in watch_root.glob("*.jsonl"):
            out.append(p)

    for root in SOURCE_HINTS:
        if not root.exists():
            continue
        if root == watch_root:
            continue

        for p in root.rglob("*"):
            if not p.is_file():
                continue
            sp = str(p)
            if "/backups/" in sp or "/logs/" in sp or "/node_modules/" in sp:
                continue

            name = p.name.lower()
            if not (name.endswith(".json") or name.endswith(".jsonl")):
                continue

            if any(tok in name for tok in ("card", "round", "event", "forecast", "watchlist", "arena")):
                out.append(p)

    return sorted(set(out), key=lambda x: str(x))



def synthesize_watchlist_card(source: Path, d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert /watchlist/active records into YES/NO forecast-card candidates.
    Safe: no model call, no state mutation, no betting.
    """
    event = str(d.get("event") or d.get("title") or "").strip()
    market = str(d.get("market") or "").strip()
    sport = str(d.get("sport") or d.get("league") or "").strip()
    event_id = str(d.get("event_id") or d.get("id") or source.stem).strip()
    start = str(d.get("start_time_utc") or d.get("deadline") or "").strip()

    if not event or not market or not event_id:
        return {}

    mlower = market.lower()

    if "moneyline" in mlower:
        if "(home)" in mlower:
            question = f"Will the home team win: {event}?"
        elif "(away)" in mlower:
            question = f"Will the away team win: {event}?"
        else:
            question = f"Will {market} win: {event}?"
    elif "over" in mlower or "under" in mlower or "total" in mlower:
        question = f"Will {market} settle in {event}?"
    else:
        question = f"Will {market} settle in {event}?"

    return {
        "card_id": event_id,
        "event_id": event_id,
        "title": question,
        "event": event,
        "sport": sport,
        "market": market,
        "deadline": start,
        "start_time_utc": start,
        "resolution_condition": f"Resolve by official final result for {event}. Market: {market}.",
        "source_url": d.get("source_url") or "",
        "estimated_fair_probability": d.get("estimated_fair_probability"),
        "ev": d.get("ev"),
        "entry_odds": d.get("entry_odds"),
        "bookmaker": d.get("bookmaker"),
        "status": d.get("status") or "",
        "schema": "aitestarena.prefilter.synthesized_watchlist_card.v1",
        "_synthesized_from_watchlist": True,
        "_source_file": str(source),
    }


def extract_candidates(paths: List[Path]) -> List[Tuple[Path, Dict[str, Any]]]:
    rows = []
    for p in paths:
        data = read_json_any(p)
        if data is None:
            continue
        for d in walk_dicts(data):
            cid = card_id(d)
            title = title_of(d)
            resolution = resolution_of(d)
            if not cid and not title:
                continue

            # Candidate must look like a forecast/card/event, not any random metadata row.
            keys = set(d.keys())
            signal_keys = {
                "card_id", "event_id", "question", "title", "resolution_condition",
                "settlement_rule", "deadline", "resolution_deadline",
                "market_probability_yes", "probability_yes", "choices", "options",
            }
            # Existing watchlist/active rows often do not have explicit YES/NO titles.
            # Convert them into candidate forecast cards before applying normal scoring.
            if "/watchlist/active/" in str(p):
                synthesized = synthesize_watchlist_card(p, d)
                if synthesized:
                    rows.append((p, synthesized))
                continue

            if not keys.intersection(signal_keys):
                continue

            if len(title) < 8 and not resolution:
                continue

            rows.append((p, d))
    return rows


def score_card(card: Dict[str, Any], seen: set) -> Tuple[int, List[str], List[str]]:
    score = 0
    reasons = []
    reject = []

    cid = card_id(card)
    title = title_of(card)
    resolution = resolution_of(card)
    text = f"{title} {resolution}".lower()
    deadline = deadline_of(card)
    prob = market_prob(card)

    if not cid:
        reject.append("missing_id")
        score -= 50

    if cid in seen:
        reject.append("already_seen_by_mini")
        score -= 100

    if is_resolved(card):
        reject.append("already_resolved")
        score -= 100

    if card.get("_synthesized_from_watchlist"):
        score += 25
        reasons.append("synthesized_yes_no_from_watchlist")
    elif is_yes_no(card):
        score += 25
        reasons.append("yes_no")
    else:
        reject.append("not_clear_yes_no")
        score -= 30

    if resolution:
        score += 20
        reasons.append("has_resolution")
    else:
        reject.append("missing_resolution")
        score -= 35

    if deadline:
        delta_days = (deadline - now_utc()).total_seconds() / 86400
        if delta_days < 0:
            reject.append("deadline_past")
            score -= 80
        elif delta_days <= 14:
            score += 20
            reasons.append("near_deadline")
        elif delta_days <= 60:
            score += 8
            reasons.append("medium_deadline")
    else:
        reject.append("missing_deadline")
        score -= 15

    # Watchlist records often store estimated_fair_probability instead of market_probability_yes.
    if prob is None:
        try:
            fp = card.get("estimated_fair_probability")
            if fp is not None and fp != "":
                x = float(fp)
                if 0 <= x <= 1:
                    prob = round(x * 100)
                elif 0 <= x <= 100:
                    prob = round(x)
        except Exception:
            pass

    if prob is not None:
        score += 15
        reasons.append("has_probability_or_fair_probability")
        if 35 <= prob <= 65:
            score += 10
            reasons.append("balanced_probability")
        elif 70 <= prob <= 95:
            score += 3
            reasons.append("strong_favorite_probability")
    else:
        if card.get("odds") or card.get("entry_odds") or card.get("market"):
            score += 8
            reasons.append("has_market_or_odds")
        else:
            score -= 8

    # EV is optional. Negative EV does not block a card-quality preview, but large positive EV is interesting.
    try:
        ev = card.get("ev")
        if ev is not None and ev != "":
            evf = float(ev)
            if evf > 2:
                score += 12
                reasons.append("positive_ev_hint")
            elif evf < -20:
                score -= 8
                reasons.append("very_negative_ev_hint")
    except Exception:
        pass

    if any(re.search(pat, text, re.I) for pat in VAGUE_PATTERNS):
        reject.append("vague_language")
        score -= 50

    if any(re.search(pat, text, re.I) for pat in INTERNAL_PATTERNS):
        reject.append("internal_or_platform_meta")
        score -= 20

    if len(title) > 220:
        score -= 5

    if not title:
        reject.append("missing_title")
        score -= 20

    return score, reasons, reject


def compact_card(card: Dict[str, Any], score: int, reasons: List[str], rejects: List[str], source: Path) -> Dict[str, Any]:
    return {
        "event_id": card_id(card),
        "title": title_of(card),
        "resolution_condition": resolution_of(card),
        "deadline": str(card.get("deadline") or card.get("resolution_deadline") or card.get("end_time") or ""),
        "market_probability_yes": market_prob(card),
        "category": card.get("category") or card.get("sport") or card.get("horizon") or "",
        "context": str(card.get("context") or card.get("description") or card.get("reason") or "")[:500],
        "prefilter_score": score,
        "prefilter_reasons": reasons,
        "prefilter_reject_flags": rejects,
        "source_file": str(source),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", action="append", help="Specific JSON/JSONL file. Can be repeated.")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-score", type=int, default=25)
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()

    paths = [Path(x) for x in args.input] if args.input else likely_source_files()
    seen = load_seen_event_ids()
    raw = extract_candidates(paths)

    scored = []
    rejected_count = 0

    for source, card in raw:
        score, reasons, rejects = score_card(card, seen)
        item = compact_card(card, score, reasons, rejects, source)
        if score >= args.min_score and "already_resolved" not in rejects and "already_seen_by_mini" not in rejects:
            scored.append(item)
        else:
            rejected_count += 1

    def _event_group_key(item):
        """
        Strictly group duplicated cards for the same real event/game.
        Handles both:
        - Will OKC Moneyline win: Oklahoma City Thunder at San Antonio Spurs (WCF G2)?
        - Will Under 218.5 settle in Oklahoma City Thunder at San Antonio Spurs (WCF G2)?
        as the same event group.
        """
        title = str(item.get("title") or "").lower()

        # Best case: our compact card kept original event.
        event = str(item.get("event") or "").lower().strip()
        if event:
            base = event
        else:
            base = title

            if " settle in " in base:
                base = base.split(" settle in ", 1)[1]
            elif ":" in base:
                base = base.split(":", 1)[1]

        base = base.replace("@", " at ")
        base = re.sub(r"\([^)]*\)", " ", base)
        base = re.sub(r"\?", " ", base)

        # Remove market words/numbers so totals and moneyline from same game collapse together.
        base = re.sub(
            r"\b(will|moneyline|win|wins|settle|home|away|team|over|under|total|spread|ml)\b",
            " ",
            base,
        )
        base = re.sub(r"\b\d+(?:\.\d+)?\b", " ", base)
        base = re.sub(r"[^a-z0-9]+", " ", base).strip()

        return base or str(item.get("event_id") or "")

    def _quality_tiebreak(item):
        title = str(item.get("title") or "").lower()
        event_id = str(item.get("event_id") or "").lower()

        score = float(item.get("prefilter_score") or 0)

        # Prefer explicit named cards over generic "home team / away team" synthesized cards.
        if "home team" in title or "away team" in title:
            score -= 8

        # Prefer readable/curated ids over hash-only ids.
        if re.match(r"^(nba|nhl|mlb|soccer)-", event_id):
            score += 5

        return score

    scored.sort(key=lambda x: (_quality_tiebreak(x), float(x.get("prefilter_score") or 0)), reverse=True)

    top = []
    used_groups = set()

    for item in scored:
        group = _event_group_key(item)
        if group in used_groups:
            continue

        top.append(item)
        used_groups.add(group)

        if len(top) >= max(1, args.top):
            break

    payload = {
        "schema": "aitestarena.mini_scout_prefilter.v1",
        "generated_at_utc": now_utc().isoformat(),
        "mode": "no_model_prefilter_only",
        "agent_profile": "mini",
        "legacy_public_agent_id": "gpt-mini",
        "cabinet_agent_id": "northstar-2fc6285f",
        "source_files_scanned": len(paths),
        "raw_candidates_seen": len(raw),
        "rejected_or_low_score": rejected_count,
        "selected_count": len(top),
        "max_cards_for_model": args.top,
        "selected_cards": top,
        "cost_guard": {
            "model_call_allowed": bool(top),
            "send_full_card_list_to_model": False,
            "max_cards_per_model_call": args.top,
            "recommended_output_token_cap": 700,
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PREFILTER_OK")
    print("source_files_scanned:", len(paths))
    print("raw_candidates_seen:", len(raw))
    print("selected_count:", len(top))
    print("out:", out)
    for i, c in enumerate(top, 1):
        print(f"{i}. score={c['prefilter_score']} id={c['event_id']} title={c['title'][:120]}")

    if args.print:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
