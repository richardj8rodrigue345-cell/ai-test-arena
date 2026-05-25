#!/usr/bin/env python3
"""
AITestArena — Direct DeepSeek Runner
=====================================
Запускается cron раз в час. Читает CSV вотчлиста, вызывает DeepSeek API,
прогоняет через guard, записывает решения в agent_decisions.csv.

Безопасность:
- no real bets, no gambling execution, no account login
- не меняет /var/www, nginx, Round 001 server
- дважды проверяет guard перед записью

Использование:
    DEEPSEEK_API_KEY=sk-... python3 direct_deepseek_runner.py
    или:
    export DEEPSEEK_API_KEY=sk-...
    python3 direct_deepseek_runner.py
    или:
    python3 direct_deepseek_runner.py --env /root/aitestarena/data/deepseek.env
"""

import os
import sys
import csv
import json
import hashlib
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
WORKSPACE = Path(os.environ.get("AITESTARENA_WORKSPACE",
    "/root/openclaw/workspace/aitestarena"))
OUTBOX = WORKSPACE / "aitestarena_watchlist_outbox"
CANDIDATE_EVENTS = OUTBOX / "candidate_events.csv"
ODDS_SNAPSHOTS = OUTBOX / "odds_snapshots.csv"
AGENT_DECISIONS = OUTBOX / "agent_decisions.csv"
LOG_FILE = WORKSPACE / "data" / "deepseek_runner.log"

# ── API ────────────────────────────────────────────────────────────────────
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

ACTIONABLE_STATE = OUTBOX / "deepseek_actionable_state.json"

_VOLATILE_KEYS = {
    "ts", "timestamp", "created_at", "updated_at", "seen_at", "last_seen_at",
    "runner_ts", "model_ts", "checked_at", "observed_at"
}

_RELEVANT_SNAPSHOT_KEYS = {
    "event_id", "market", "bookmaker", "source", "source_name", "source_url",
    "american_odds", "decimal_odds", "line", "outcome", "notes", "status",
    "result", "settlement", "deadline"
}

def _stable_row(row):
    """Return row without timestamp-like volatile fields."""
    return {
        str(k): str(v)
        for k, v in sorted((row or {}).items())
        if str(k).lower() not in _VOLATILE_KEYS and str(v) != ""
    }

def _snapshot_key(row):
    return {
        str(k): str(v)
        for k, v in sorted((row or {}).items())
        if str(k) in _RELEVANT_SNAPSHOT_KEYS and str(v) != ""
    }

# AITESTARENA_PROMPT_AWARE_FINGERPRINT_20260525_V2
def _prompt_source_fingerprint_payload():
    """Hash active prompt/source files so prompt changes trigger DeepSeek again."""
    files = [
        WORKSPACE / "AGENTS.md",
        WORKSPACE / "HEARTBEAT.md",
        WORKSPACE / "tasks" / "DEEPSEEK_WATCHLIST_CURRENT_TASK.md",
        WORKSPACE / "tasks" / "DEEPSEEK_WATCHLIST_HOURLY_PROMPT.md",
        WORKSPACE / "direct_deepseek_runner.py",
    ]
    out = {}
    for fp in files:
        key = str(fp.relative_to(WORKSPACE)) if str(fp).startswith(str(WORKSPACE)) else str(fp)
        try:
            data = fp.read_bytes()
            out[key] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        except Exception as e:
            out[key] = {"error": type(e).__name__}

    try:
        sp = SYSTEM_PROMPT
    except NameError:
        sp = ""
    out["SYSTEM_PROMPT"] = {
        "sha256": hashlib.sha256(sp.encode("utf-8")).hexdigest(),
        "size": len(sp),
    }
    return out


def _actionable_fingerprint(active_candidates, odds_context):
    """
    Fingerprint actionable state plus active prompt/source hash.
    Candidate timestamps are ignored, but prompt/instruction changes trigger model calls.
    """
    items = []
    for c in active_candidates:
        eid = c.get("event_id", "")
        snaps = odds_context.get(eid, []) or []

        uniq = {}
        for snap in snaps:
            sk = _snapshot_key(snap)
            if sk:
                uniq[json.dumps(sk, sort_keys=True, ensure_ascii=False)] = sk

        items.append({
            "candidate": _stable_row(c),
            "snapshots": [uniq[k] for k in sorted(uniq.keys())],
        })

    fingerprint_obj = {
        "actionable_items": items,
        "prompt_sources": _prompt_source_fingerprint_payload(),
    }
    payload = json.dumps(fingerprint_obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), payload

def _load_actionable_state():
    try:
        return json.loads(ACTIONABLE_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_actionable_state(fingerprint, payload, run_ts, analysed_count):
    ACTIONABLE_STATE.write_text(json.dumps({
        "fingerprint": fingerprint,
        "run_ts": run_ts,
        "analysed_count": analysed_count,
        "payload_size": len(payload),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = int(os.environ.get("DEEPSEEK_TIMEOUT", "30"))

# ── Guards / Limits ───────────────────────────────────────────────────────
MAX_CANDIDATES_PER_RUN = 10
MIN_SOURCES_FOR_ENTRY = 2
MAX_SOURCE_AGE_HOURS = 24  # старые снепшоты не используем

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("deepseek-runner")


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _read_csv(path: Path) -> list[dict]:
    """Читает CSV, возвращает список словарей."""
    if not path.exists():
        log.warning("Файл не найден: %s", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    log.info("Прочитано %d строк из %s", len(rows), path.name)
    return rows


def _append_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    """Дописывает строки в CSV. Создаёт файл с заголовком если его нет."""
    if not rows:
        return
    file_exists = path.exists() and path.stat().st_size > 0
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0].keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    log.info("Дописано %d строк в %s", len(rows), path.name)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ═══════════════════════════════════════════════════════════════════════════
#  DEEPSEEK API CALL
# ═══════════════════════════════════════════════════════════════════════════

def call_deepseek(system_prompt: str, user_prompt: str, api_key: str) -> dict:
    """Вызывает DeepSeek Chat API. Возвращает сырой ответ."""
    import requests

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    log.info("Вызов DeepSeek (%s)...", DEEPSEEK_BASE_URL)
    resp = requests.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=DEEPSEEK_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    raw_text = data["choices"][0]["message"]["content"]
    log.info("DeepSeek ответил: %d токенов", data["usage"]["total_tokens"])
    return json.loads(raw_text)


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
[AITESTARENA_DEEPSEEK_CABINET_CONTEXT_20260525]
DeepSeek cabinet/profile context:
- public agent: DeepSeek
- cabinet/profile agent_id: aitestarena-operator-deepseek-run-demo-ceb79955
- safe cabinet/profile URL without token: https://aitestarena.com/agents/cabinet/?agent_id=aitestarena-operator-deepseek-run-demo-ceb79955
Never include cabinet token or private magic link in prompt, logs, GitHub, NotebookLM, or reports.
Objective: grow virtual paper bankroll over time through disciplined positive-EV paper-only ENTER decisions when guards pass; otherwise WAIT or SKIP with clear reason.

Вы AITestArena — система paper-мониторинга спортивных линий.
Ваша задача: анализировать события из вотчлиста и принимать решения.

Формат ответа — JSON:

{
    "decisions": [
        {
            "event_id": "...",
            "market": "...",
            "status": "ENTER|WAIT|SKIP|NO_VALUE|NEEDS_SECOND_SOURCE|EXPIRED_SECOND_SOURCE",
            "reason": "короткое объяснение",
            "estimated_fair_probability": 0.0 или null,
            "ev": 0.0 или null,
            "kelly_fraction": 0.0 или null,
            "suggested_paper_allocation": 0 или число,
            "sources_found": число,
            "source_names": ["..."],
            "notes": ""
        }
    ]
}

Правила (строго):
- ENTER запрещён при 1 источнике → WAIT / NEEDS_SECOND_SOURCE
- ENTER запрещён если нет fair_probability
- ENTER запрещён если EV <= 0 или Kelly <= 0
- Если дедлайн прошёл без 2+ источников → EXPIRED_SECOND_SOURCE / NO_ENTRY
- Если fair probability <= breakeven → SKIP / NO_VALUE
- Только paper, virtual credits. Реальных ставок нет.
- Не менять /var/www, nginx, Round 001 server напрямую.
- CONFIRMED_LINE ≠ автоматическая ставка — нужен положительный EV.
- Результат матча для EXPIRED_SECOND_SOURCE — info-only, не в paper ROI."""


# ═══════════════════════════════════════════════════════════════════════════
#  GUARD проверка перед записью
# ═══════════════════════════════════════════════════════════════════════════

def guard_check(decision: dict, candidate_row: dict | None) -> dict:
    """
    Дважды проверяет решение перед записью.
    Возвращает {'status': 'PASS', 'decision': decision} или BLOCKED с причиной.
    """
    eid = decision.get("event_id", "?")
    status = decision.get("status", "")
    sources = decision.get("sources_found", 0)
    fair_prob = decision.get("estimated_fair_probability")
    ev = decision.get("ev")
    kelly = decision.get("kelly_fraction")

    # Guard 1: ENTER при < 2 источников
    if status == "ENTER" and sources < MIN_SOURCES_FOR_ENTRY:
        return {"status": "BLOCKED", "reason": f"[GUARD] ENTER blocked: only {sources} source(s), need >=2",
                "fix_to": "NEEDS_SECOND_SOURCE"}

    # Guard 2: ENTER без fair_probability
    if status == "ENTER" and fair_prob is None:
        return {"status": "BLOCKED", "reason": "[GUARD] ENTER blocked: no fair_probability",
                "fix_to": "WAIT"}

    # Guard 3: ENTER без положительного EV
    if status == "ENTER" and (ev is None or float(ev) <= 0):
        return {"status": "BLOCKED", "reason": f"[GUARD] ENTER blocked: EV={ev} <= 0",
                "fix_to": "SKIP"}

    # Guard 4: ENTER без положительного Kelly
    if status == "ENTER" and (kelly is None or float(kelly) <= 0):
        return {"status": "BLOCKED", "reason": f"[GUARD] ENTER blocked: Kelly={kelly} <= 0",
                "fix_to": "SKIP"}

    # Guard 5: Если candidate имеет deadline <= now и sources < 2 → EXPIRED
    if candidate_row and fair_prob is None and status not in ("EXPIRED_SECOND_SOURCE", "RESOLVED"):
        start_time = candidate_row.get("start_time_utc", "")
        if start_time and start_time < _now_utc() and sources < 2:
            return {"status": "BLOCKED", "reason": f"[GUARD] Deadline passed with {sources} source(s)",
                    "fix_to": "EXPIRED_SECOND_SOURCE"}

    return {"status": "PASS", "decision": decision}


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    run_ts = _now_utc()
    log.info("=" * 60)
    log.info("=== DeepSeek Runner START at %s ===", run_ts)

    # ── API Key ────────────────────────────────────────────────────────
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        # Try loading from env file
        env_file = os.environ.get("DEEPSEEK_ENV_FILE", "/root/aitestarena/data/deepseek.env")
        if Path(env_file).exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("\"'")
                        log.info("API key загружен из %s", env_file)
                        break

    if not api_key:
        log.error("DEEPSEEK_API_KEY не найден! Установите переменную или --env файл.")
        sys.exit(1)

    # ── Read inputs ────────────────────────────────────────────────────
    candidates = _read_csv(CANDIDATE_EVENTS)
    if not candidates:
        log.info("Нет кандидатов для анализа. Выход.")
        return

    # ── Filter active candidates ───────────────────────────────────────
    active_statuses = {"ACTIVE", "WAIT", "NEEDS_SECOND_SOURCE", "CONFIRMED_LINE", "PAPER_WATCHLIST_NEEDS_SECOND_SOURCE"}
    active = [r for r in candidates if r.get("decision_status", "") in active_statuses]
    active = active[:MAX_CANDIDATES_PER_RUN]
    log.info("Активных кандидатов: %d (лимит: %d)", len(active), MAX_CANDIDATES_PER_RUN)

    if not active:
        log.info("Нет активных. Выход.")
        return

    # ── Read odds context ──────────────────────────────────────────────
    snapshots = _read_csv(ODDS_SNAPSHOTS)
    # Group by event_id for context
    odds_context = {}
    for s in snapshots:
        eid = s.get("event_id", "")
        if eid not in odds_context:
            odds_context[eid] = []
        odds_context[eid].append(s)
    log.info("Контекст линий: %d событий", len(odds_context))

    # ── Build prompt ───────────────────────────────────────────────────
    prompt_lines = ["## Текущий вотчлист (активные события):"]
    for i, row in enumerate(active, 1):
        eid = row.get("event_id", "?")
        prompt_lines.append(f"\n### {i}. {eid}")
        prompt_lines.append(f"- Спорт: {row.get('sport', '?')}")
        prompt_lines.append(f"- Команды: {row.get('event', '?')}")
        prompt_lines.append(f"- Рынок: {row.get('market', '?')}")
        prompt_lines.append(f"- Статус: {row.get('decision_status', '?')}")
        prompt_lines.append(f"- Коэфф: {row.get('best_bookmaker', '?')} @ {row.get('best_decimal_odds', '?')}")
        prompt_lines.append(f"- Breakeven: {row.get('breakeven_probability', '?')}")
        prompt_lines.append(f"- Fair prob: {row.get('estimated_fair_probability', '?')}")
        prompt_lines.append(f"- EV: {row.get('ev', '?')}")
        prompt_lines.append(f"- Kelly: {row.get('kelly_fraction', '?')}")
        prompt_lines.append(f"- Старт (UTC): {row.get('start_time_utc', '?')}")
        prompt_lines.append(f"- Почему: {row.get('why_interesting', '')}")
        prompt_lines.append(f"- Риски: {row.get('main_risk', '')}")

        # Добавляем линии из снепшотов
        eid_snapshots = odds_context.get(eid, [])
        if eid_snapshots:
            prompt_lines.append(f"- Snapshot-линии ({len(eid_snapshots)}):")
            for s in eid_snapshots[-5:]:  # последние 5
                prompt_lines.append(f"  · {s.get('bookmaker','?')}: {s.get('american_odds','?')} / {s.get('decimal_odds','?')} / {s.get('notes','')}")

    user_prompt = "\n".join(prompt_lines)
    user_prompt += "\n\nОцени каждое активное событие. Верни JSON с полем 'decisions'."

    # ── Actionable guard before paid DeepSeek call ─────────────────────
    fingerprint_context = (
        locals().get("context")
        or locals().get("odds_context")
        or locals().get("line_context")
        or {}
    )
    current_fingerprint, fingerprint_payload = _actionable_fingerprint(active, fingerprint_context)
    prev_state = _load_actionable_state()
    if prev_state.get("fingerprint") == current_fingerprint:
        log.info("skip_no_actionable_changes: fingerprint unchanged, DeepSeek API not called")
        log.info("previous_actionable_run_ts: %s", prev_state.get("run_ts"))
        log.info("=" * 60)
        log.info("=== RUN SUMMARY ===")
        log.info("Candidates analysed: %d", len(active))
        log.info("Decisions written:   0")
        log.info("Guard blocks:        0")
        log.info("Files updated:       none")
        log.info("=== RUN END ===")
        log.info("=" * 60)
        sys.exit(0)

    # ── Call DeepSeek ──────────────────────────────────────────────────
    try:
        result = call_deepseek(SYSTEM_PROMPT, user_prompt, api_key)
    except Exception as e:
        log.error("Ошибка вызова DeepSeek: %s", str(e))
        sys.exit(2)

    decisions = result.get("decisions", [])
    if not decisions:
        log.warning("DeepSeek не вернул decisions. Ответ: %s", json.dumps(result)[:500])
        sys.exit(3)

    # ── Guard each decision ────────────────────────────────────────────
    guarded_decisions = []
    blocked = []

    for dec in decisions:
        eid = dec.get("event_id", "")
        candidate_row = next((c for c in candidates if c.get("event_id") == eid), None)
        check = guard_check(dec, candidate_row)

        if check["status"] == "BLOCKED":
            blocked.append(check)
            # Fix status if suggested
            if "fix_to" in check:
                dec["status"] = check["fix_to"]
                dec["reason"] = f"{check['reason']}. Status auto-corrected to {check['fix_to']}."
                check = guard_check(dec, candidate_row)  # re-check
                if check["status"] == "BLOCKED":
                    log.warning("[GUARD] %s — всё ещё BLOCKED после фикса: %s", eid, check["reason"])
                    dec["status"] = "SKIP"
                    dec["reason"] = f"[GUARD OVERRIDE] {check['reason']}"

        guarded_decisions.append(dec)
        log.info("[GUARD] %s → status=%s, EV=%s, Kelly=%s",
                 eid, dec.get("status"), dec.get("ev"), dec.get("kelly_fraction"))

    # ── Enrich and write ───────────────────────────────────────────────
    for dec in guarded_decisions:
        dec["runner_ts"] = run_ts
        dec.setdefault("notes", "")
        dec.setdefault("source_names", "")
        if isinstance(dec.get("source_names"), list):
            dec["source_names"] = "; ".join(dec["source_names"])

    _append_csv(AGENT_DECISIONS, guarded_decisions)
    _save_actionable_state(current_fingerprint, fingerprint_payload, run_ts, len(active))
    log.info("actionable_fingerprint_saved: %s", current_fingerprint[:12])

    # ── Run post-processing scripts ────────────────────────────────────
    scripts = [
        WORKSPACE / "import_agent_decisions_outbox.py",
        WORKSPACE / "render_agents_leaderboard.py",
        WORKSPACE / "process_watchlist_outbox.py",
    ]

    for script in scripts:
        if script.exists():
            log.info("Запуск %s...", script.name)
            ret = os.system(f"cd {WORKSPACE} && python3 {script} 2>&1")
            log.info("%s завершился с кодом %d", script.name, ret)
        else:
            log.warning("Скрипт не найден: %s", script)

    # ── Summary ────────────────────────────────────────────────────────
    enters = sum(1 for d in guarded_decisions if d.get("status") == "ENTER")
    waits = sum(1 for d in guarded_decisions if "WAIT" in d.get("status", "").upper())
    skips = sum(1 for d in guarded_decisions if d.get("status") in ("SKIP", "NO_VALUE"))
    expires = sum(1 for d in guarded_decisions if "EXPIRED" in d.get("status", "").upper())

    log.info("=" * 60)
    log.info("=== RUN SUMMARY ===")
    log.info("Candidates analysed: %d", len(active))
    log.info("Decisions written:   %d", len(guarded_decisions))
    log.info("  ENTER:             %d", enters)
    log.info("  WAIT:              %d", waits)
    log.info("  SKIP/NO_VALUE:     %d", skips)
    log.info("  EXPIRED:           %d", expires)
    log.info("Guard blocks:        %d", len(blocked))
    log.info("Files updated:       %s", AGENT_DECISIONS.name)
    log.info("=== RUN END ===")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
