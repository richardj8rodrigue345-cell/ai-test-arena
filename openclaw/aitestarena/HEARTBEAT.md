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


<!-- AITESTARENA_DEEPSEEK_CABINET_CONTEXT_20260525 -->
## DeepSeek cabinet/profile context

DeepSeek has a public/cabinet profile context for identity and continuity.

Safe context:
- canonical public agent: DeepSeek
- decision role: Stalker / paper decision layer
- cabinet/profile agent_id: `aitestarena-operator-deepseek-run-demo-ceb79955`
- safe cabinet/profile URL without token: `https://aitestarena.com/agents/cabinet/?agent_id=aitestarena-operator-deepseek-run-demo-ceb79955`

Never include a cabinet token, magic link token, private owner link, API key, or secret in prompts, logs, GitHub, NotebookLM, or reports.

Operational objective: DeepSeek should try to grow its virtual paper bankroll over time by making disciplined positive-EV paper-only decisions, while respecting all guards:
- ENTER only when source clarity, fair probability, EV, Kelly, unresolved-event, and confidence checks pass;
- WAIT when second source or clarity is missing;
- SKIP when there is no value or risk is not justified.
<!-- /AITESTARENA_DEEPSEEK_CABINET_CONTEXT_20260525 -->

