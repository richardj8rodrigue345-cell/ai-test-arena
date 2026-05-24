#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

snap = Path("/root/openclaw/workspace/aitestarena/state/controller_snapshots")
snap.mkdir(parents=True, exist_ok=True)

def load_json(path):
    p = Path(path)
    if not p.exists():
        return {"_exists": False, "_path": str(p)}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            d["_exists"] = True
            d["_path"] = str(p)
            return d
        return {"_exists": True, "_path": str(p), "_type": type(d).__name__}
    except Exception as e:
        return {"_exists": True, "_path": str(p), "_error": str(e)}

public = load_json("/root/aitestarena/state/aitestarena_public_pipeline_latest.json")
mini = load_json("/root/aitestarena/state/mini_scout_internal_pipeline_latest.json")
gpt_input = load_json("/root/aitestarena/state/mini_scout_gpt_input_latest.json")

cron_pipelines = Path("/etc/cron.d/aitestarena_pipelines")
cron_heartbeat = Path("/etc/cron.d/aitestarena_heartbeat")

payload = {
    "schema": "aitestarena.sentinel_controller_snapshot.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_truth": "root host",
    "public_pipeline": {
        "status": public.get("status"),
        "writes_public_vitrina": public.get("writes_public_vitrina"),
        "calls_gpt": public.get("calls_gpt"),
        "writes_agent_decisions": public.get("writes_agent_decisions"),
        "process_rc": public.get("process_rc"),
        "render_rc": public.get("render_rc"),
        "source_path": public.get("_path"),
        "exists": public.get("_exists", False),
    },
    "mini_internal_pipeline": {
        "status": mini.get("status"),
        "writes_public_vitrina": mini.get("writes_public_vitrina"),
        "public_watchlist_changed": mini.get("public_watchlist_changed"),
        "calls_gpt": mini.get("calls_gpt"),
        "writes_agent_decisions": mini.get("writes_agent_decisions"),
        "mini_scout": mini.get("mini_scout"),
        "source_path": mini.get("_path"),
        "exists": mini.get("_exists", False),
    },
    "gpt_input": {
        "mode": gpt_input.get("mode"),
        "model_target": gpt_input.get("model_target"),
        "cards_count": len(gpt_input.get("cards") or []),
        "model_called_by_this_script": gpt_input.get("cost_guard", {}).get(
            "model_called_by_this_script",
            gpt_input.get("model_called_by_this_script")
        ),
        "source_path": gpt_input.get("_path"),
        "exists": gpt_input.get("_exists", False),
    },
    "cron": {
        "aitestarena_pipelines_exists": cron_pipelines.exists(),
        "aitestarena_pipelines_text": cron_pipelines.read_text(encoding="utf-8", errors="replace") if cron_pipelines.exists() else "",
        "aitestarena_heartbeat_exists": cron_heartbeat.exists(),
        "aitestarena_heartbeat_text": cron_heartbeat.read_text(encoding="utf-8", errors="replace") if cron_heartbeat.exists() else "",
    },
    "expected_ok": {
        "public_pipeline": {
            "status": "DONE",
            "writes_public_vitrina": True,
            "calls_gpt": False,
            "writes_agent_decisions": False
        },
        "mini_internal_pipeline": {
            "status": "DONE",
            "writes_public_vitrina": False,
            "public_watchlist_changed": False,
            "calls_gpt": False,
            "writes_agent_decisions": False
        },
        "gpt_input": {
            "cards_count_max": 3,
            "mode": "dry_run_input_only_no_model_call"
        }
    },
    "sentinel_boundaries": [
        "read-only",
        "do not edit cron",
        "do not edit production files",
        "do not run renderer",
        "do not run GPT",
        "do not write agent_decisions",
        "do not repair automatically"
    ]
}

out = snap / "aitestarena_pipeline_controller_snapshot_latest.json"
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

(snap / "README_SENTINEL.md").write_text(
    "Sentinel should read aitestarena_pipeline_controller_snapshot_latest.json only. Read-only controller report only.\n",
    encoding="utf-8"
)

print("OK snapshot_written", out)
print("public_status", payload["public_pipeline"]["status"])
print("mini_status", payload["mini_internal_pipeline"]["status"])
print("gpt_input_cards", payload["gpt_input"]["cards_count"])
