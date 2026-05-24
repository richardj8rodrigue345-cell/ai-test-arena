#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/aitestarena"
TOOLS="$ROOT/tools"
STATE="$ROOT/state"
LOGS="$ROOT/logs"
LOCK="$STATE/mini_scout_cycle.lock"

mkdir -p "$STATE" "$LOGS"

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "MINI_SCOUT_CYCLE_ALREADY_RUNNING"
  exit 0
fi

RUN_ID="$(date -u +%Y%m%d-%H%M%S)"
PREFILTER_JSON="$STATE/mini_scout_prefilter_latest.json"
CYCLE_JSON="$STATE/mini_scout_cycle_latest.json"
PREFILTER_LOG="$LOGS/mini_scout_prefilter_${RUN_ID}.txt"

echo "=== Mini Scout cycle ==="
echo "run_id=$RUN_ID"
echo

echo "=== Stage 1: identity guard ==="
if [ -x "$TOOLS/enforce_mini_scout_identity.py" ]; then
  /usr/bin/python3 "$TOOLS/enforce_mini_scout_identity.py" >/dev/null 2>&1 || echo "WARN: identity guard failed"
  echo "identity_guard=ran"
else
  echo "identity_guard=missing"
fi
echo

echo "=== Stage 2: prefilter, no GPT call ==="
/usr/bin/python3 "$TOOLS/select_interesting_cards.py" --top 3 --min-score 20 > "$PREFILTER_LOG" 2>&1
cat "$PREFILTER_LOG"
echo

echo "=== Stage 3: cycle decision ==="
/usr/bin/python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone

pref = Path("/root/aitestarena/state/mini_scout_prefilter_latest.json")
out = Path("/root/aitestarena/state/mini_scout_cycle_latest.json")

d = json.loads(pref.read_text(encoding="utf-8"))
cards = d.get("selected_cards") or []
selected_count = len(cards)

status = "DRY_RUN_READY_NO_MODEL_CALL_YET" if selected_count else "STOP_NO_CANDIDATES_NO_MODEL_CALL"

payload = {
    "schema": "aitestarena.mini_scout_cycle.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "selected_count": selected_count,
    "model_called": False,
    "paper_decision_written": False,
    "csv_modified": False,
    "selected_cards": cards,
    "safety": {
        "no_gpt_call_in_this_cycle": True,
        "no_real_money": True,
        "virtual_credits_only": True
    }
}

out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("cycle_status:", status)
print("selected_count:", selected_count)
print("model_called:", False)

for i, c in enumerate(cards, 1):
    print(f"{i}. {c.get('event_id')} | score={c.get('prefilter_score')} | {c.get('title')}")
PY

echo
echo
echo "=== Stage 4: prepare compact GPT input, still no GPT call ==="
/usr/bin/python3 "$TOOLS/prepare_mini_scout_gpt_input.py"

echo "latest=$CYCLE_JSON"
