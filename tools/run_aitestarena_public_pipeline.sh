#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/aitestarena"
TOOLS="$ROOT/tools"
STATE="$ROOT/state"
LOGS="$ROOT/logs"
LOCK="$STATE/aitestarena_public_pipeline.lock"
mkdir -p "$STATE" "$LOGS"

exec 9>"$LOCK"
flock -n 9 || { echo "PUBLIC_PIPELINE_ALREADY_RUNNING"; exit 0; }

RUN_ID="$(date -u +%Y%m%d-%H%M%S)"
LOG="$LOGS/aitestarena_public_pipeline_${RUN_ID}.log"

{
  echo "=== PUBLIC pipeline ==="
  echo "run_id=$RUN_ID"

  PROCESS_RC="missing"
  if [ -x "$TOOLS/run_watchlist_data_only_guarded.sh" ]; then
    set +e
    timeout 180s "$TOOLS/run_watchlist_data_only_guarded.sh" --run
    PROCESS_RC="$?"
    set -e
  fi
  echo "process_rc=$PROCESS_RC"

  RENDER_RC="missing"
  if [ -f "$TOOLS/render_watchlist_public_safe.py" ]; then
    set +e
    /usr/bin/python3 "$TOOLS/render_watchlist_public_safe.py"
    RENDER_RC="$?"
    set -e
  fi
  echo "render_rc=$RENDER_RC"

  /usr/bin/python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone

payload = {
  "schema": "aitestarena.public_pipeline.v1",
  "generated_at_utc": datetime.now(timezone.utc).isoformat(),
  "run_id": "$RUN_ID",
  "status": "DONE" if "$PROCESS_RC" == "0" and "$RENDER_RC" == "0" else "WARN",
  "process_rc": "$PROCESS_RC",
  "render_rc": "$RENDER_RC",
  "writes_public_vitrina": True,
  "calls_gpt": False,
  "writes_agent_decisions": False,
  "log": "$LOG"
}
Path("/root/aitestarena/state/aitestarena_public_pipeline_latest.json").write_text(
  json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY
} | tee "$LOG"
