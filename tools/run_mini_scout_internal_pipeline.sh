#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/aitestarena"
TOOLS="$ROOT/tools"
STATE="$ROOT/state"
LOGS="$ROOT/logs"
LOCK="$STATE/mini_scout_internal_pipeline.lock"
mkdir -p "$STATE" "$LOGS"

exec 9>"$LOCK"
flock -n 9 || { echo "MINI_INTERNAL_ALREADY_RUNNING"; exit 0; }

RUN_ID="$(date -u +%Y%m%d-%H%M%S)"
LOG="$LOGS/mini_scout_internal_pipeline_${RUN_ID}.log"

HTML="/var/www/aitestarena/watchlist/index.html"
JSON="/var/www/aitestarena/data/watchlist.json"

mt() { [ -e "$1" ] && stat -c '%Y' "$1" || echo missing; }

HTML_BEFORE="$(mt "$HTML")"
JSON_BEFORE="$(mt "$JSON")"

{
  echo "=== MINI INTERNAL pipeline ==="
  echo "run_id=$RUN_ID"
  echo "html_before=$HTML_BEFORE"
  echo "json_before=$JSON_BEFORE"

  MINI_RC="missing"
  if [ -x "$TOOLS/run_mini_scout_cycle.sh" ]; then
    set +e
    timeout 120s "$TOOLS/run_mini_scout_cycle.sh"
    MINI_RC="$?"
    set -e
  fi

  HTML_AFTER="$(mt "$HTML")"
  JSON_AFTER="$(mt "$JSON")"

  echo "mini_rc=$MINI_RC"
  echo "html_after=$HTML_AFTER"
  echo "json_after=$JSON_AFTER"

  PUBLIC_CHANGED=false
  if [ "$HTML_BEFORE" != "$HTML_AFTER" ] || [ "$JSON_BEFORE" != "$JSON_AFTER" ]; then
    PUBLIC_CHANGED=true
  fi

  /usr/bin/python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone

def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}

cycle = load("/root/aitestarena/state/mini_scout_cycle_latest.json")
gpt_input = load("/root/aitestarena/state/mini_scout_gpt_input_latest.json")

payload = {
  "schema": "aitestarena.mini_scout_internal_pipeline.v1",
  "generated_at_utc": datetime.now(timezone.utc).isoformat(),
  "run_id": "$RUN_ID",
  "status": "DONE" if "$MINI_RC" == "0" and "$PUBLIC_CHANGED" == "false" else "WARN",
  "mini_rc": "$MINI_RC",
  "public_watchlist_changed": "$PUBLIC_CHANGED" == "true",
  "writes_public_vitrina": False,
  "calls_gpt": False,
  "writes_agent_decisions": False,
  "mini_scout": {
    "cycle_status": cycle.get("status"),
    "selected_count": cycle.get("selected_count"),
    "model_called": cycle.get("model_called"),
    "paper_decision_written": cycle.get("paper_decision_written"),
    "gpt_input_cards": len(gpt_input.get("cards") or []),
    "gpt_input_mode": gpt_input.get("mode")
  },
  "log": "$LOG"
}
Path("/root/aitestarena/state/mini_scout_internal_pipeline_latest.json").write_text(
  json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY
} | tee "$LOG"
