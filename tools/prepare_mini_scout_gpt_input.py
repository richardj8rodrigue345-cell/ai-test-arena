#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

cycle_path = Path("/root/aitestarena/state/mini_scout_cycle_latest.json")
out = Path("/root/aitestarena/state/mini_scout_gpt_input_latest.json")

cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
cards = cycle.get("selected_cards") or []

payload = {
    "schema": "aitestarena.mini_scout_gpt_input.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "workflow": "Mini Arena Scout",
    "model_target": "gpt-5.5",
    "mode": "dry_run_input_only_no_model_call",
    "agent_profile": {
        "display_name": "Mini Arena Scout",
        "legacy_public_agent_id": "gpt-mini",
        "cabinet_agent_id": "northstar-2fc6285f"
    },
    "task": "Analyze only these shortlisted paper forecast cards. Return JSON. Do not place bets. Do not write state. Virtual credits only.",
    "cost_guard": {
        "max_cards": 3,
        "no_full_watchlist": True,
        "output_token_cap_recommended": 700,
        "model_called_by_this_script": False
    },
    "cards": [
        {
            "event_id": c.get("event_id"),
            "title": c.get("title"),
            "resolution_condition": c.get("resolution_condition"),
            "deadline": c.get("deadline"),
            "market_probability_yes": c.get("market_probability_yes"),
            "category": c.get("category"),
            "context": c.get("context"),
            "prefilter_score": c.get("prefilter_score"),
            "prefilter_reasons": c.get("prefilter_reasons"),
            "risk_flags": c.get("prefilter_reject_flags"),
            "source_file": c.get("source_file")
        }
        for c in cards
    ],
    "required_output": {
        "action": "BET/SKIP/NEEDS_MORE_DATA",
        "event_id": "string or null",
        "selected_side": "YES/NO/null",
        "probability": "0-1 or null",
        "confidence": "low/medium/high",
        "stake_units": "0 or small test unit",
        "reason": "short",
        "risk_flags": [],
        "needs_more_data": False
    }
}

out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("gpt_input_written:", out)
print("cards_for_model:", len(cards))
print("model_called:", False)
