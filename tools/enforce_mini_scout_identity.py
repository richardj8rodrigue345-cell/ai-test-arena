#!/usr/bin/env python3
import json
import re
from pathlib import Path

LEGACY_ID = "gpt-mini"
DISPLAY_NAME = "Mini Arena Scout"
DISPLAY_MODEL = "GPT-5.5"
TOTAL_BANKROLL = 1000.0

JSONS = [
    Path("/root/aitestarena/agents/registry.json"),
    Path("/root/aitestarena/agents/gpt-mini/bankroll.json"),
    Path("/var/www/aitestarena/data/agents.json"),
    Path("/var/www/aitestarena/data/agents/gpt-mini/bankroll.json"),
    Path("/root/firstmeet_github_upload/site/aitestarena/data/agents.json"),
    Path("/root/firstmeet_github_upload/site/aitestarena/data/agents/gpt-mini/bankroll.json"),
]

HTMLS = [
    Path("/var/www/aitestarena/agents/index.html"),
    Path("/root/firstmeet_github_upload/site/aitestarena/agents/index.html"),
]

def is_gptmini_obj(obj):
    return isinstance(obj, dict) and obj.get("agent_id") == LEGACY_ID

def walk(obj):
    if isinstance(obj, dict):
        if is_gptmini_obj(obj):
            if "agent_name" in obj:
                obj["agent_name"] = DISPLAY_NAME
            if "name" in obj:
                obj["name"] = DISPLAY_NAME
            if "model" in obj:
                obj["model"] = DISPLAY_MODEL
            obj["display_name"] = DISPLAY_NAME
            obj["display_model"] = DISPLAY_MODEL

        # durable display invariant: total bankroll is starting budget, not current equity
        if "total_bankroll" in obj:
            obj["total_bankroll"] = TOTAL_BANKROLL
        if "starting_bankroll" in obj:
            obj["starting_bankroll"] = TOTAL_BANKROLL
        if "starting_virtual_credits" in obj:
            obj["starting_virtual_credits"] = TOTAL_BANKROLL

        for v in obj.values():
            walk(v)

    elif isinstance(obj, list):
        for x in obj:
            walk(x)

for p in JSONS:
    if not p.exists():
        continue
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        walk(d)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("json_ok:", p)
    except Exception as e:
        print("json_skip:", p, e)

for p in HTMLS:
    if not p.exists():
        continue

    s = p.read_text(encoding="utf-8", errors="ignore")

    # Only visible display labels; keep <code>gpt-mini</code> and agent_id unchanged.
    s = s.replace("<h3>GPT-mini</h3>", "<h3>Mini Arena Scout</h3>")
    s = s.replace("<h3>GPT mini</h3>", "<h3>Mini Arena Scout</h3>")
    s = s.replace("<p class='model'>GPT-mini</p>", "<p class='model'>GPT-5.5</p>")
    s = s.replace("<p class='model'>GPT mini</p>", "<p class='model'>GPT-5.5</p>")
    s = s.replace("<p class=\"model\">GPT-mini</p>", "<p class=\"model\">GPT-5.5</p>")
    s = s.replace("<p class=\"model\">GPT mini</p>", "<p class=\"model\">GPT-5.5</p>")

    # Keep Total bankroll display fixed.
    s = re.sub(
        r"<strong>[-+]?\d+(?:\.\d+)?</strong><span>Total bankroll</span>",
        "<strong>1000</strong><span>Total bankroll</span>",
        s,
    )

    p.write_text(s, encoding="utf-8")
    print("html_ok:", p)

print("MINI_SCOUT_IDENTITY_ENFORCED")
