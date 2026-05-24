# Heartbeat Tasks

## 1. Соккер-скан (каждый heartbeat, каждые ~30 мин)
- Запустить: `. state/theoddsapi_env.sh && python3 arena_soccer_scan.py`
- Анализирует Brazil Série A/B, Chile, MLS, Copa Sudamericana, MLB, WNBA, FIFA WC
- Ищет расхождения >1.5% между книгами по implied probability
- Добавляет кандидатов в `aitestarena_watchlist_outbox/candidate_events.csv`
- Если найден хотя бы 1 кандидат — написать краткий отчёт (топ-3)

## 2. Проверка The Odds API лимита
- Проверить `x-requests-remaining` header
- Если <50 — предупредить

## 3. Сводка
Написать: "🧪 Соккер-скан: N кандидатов. Топ: ..."

---

## AITESTARENA_STALKER_PAPER_ENTRY_RULE_20260525

After the scan updates candidate events, Stalker may also prepare a paper-only decision candidate.

Output path:

`aitestarena_watchlist_outbox/agent_decisions.csv`

CSV format:

`agent_id,event_id,decision,allocation,reason,created_at_utc`

Allowed decisions:

- ENTER
- WAIT
- SKIP

Use ENTER only if the event is clear, unresolved, not duplicated, and suitable for virtual-credit paper tracking.

Use WAIT if a second source / clearer data / later check is needed.

Use SKIP if no value, unclear event, missing source, already started, or low confidence.

Do not write bankroll files directly.

Do not settle positions directly.

Do not render public pages.

The 07-cycle imports decisions, settles positions, and renders public agent state.

