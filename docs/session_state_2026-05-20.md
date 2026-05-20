# AITestArena / FirstMeet — состояние сессии 2026-05-20

## Зачем сохранено
Пользователь попросил сохранить состояние на Google Drive и GitHub, потому что работа шла тяжело, были ошибки в масштабе изменений и повторяющиеся поломки. Этот документ фиксирует факты без секретов и без длинных логов.

## AITestArena — текущая продуктовая линия
AITestArena должен быть практичным сервисом проверки AI-агентов на реальных внешних событиях с odds/sports источниками. Цель: найти агентов, чьи прогнозы можно использовать как копируемый сигнал. Внутренние platform_meta / GitHub stars / agent-count вопросы больше не использовать для benchmark round.

Правило вопросов:
- сначала Polymarket;
- затем Kalshi;
- если там нет коротких нормальных рынков — искать крупные odds / sportsbook / odds aggregators;
- горизонт: 1–3 суток, максимум 7 дней;
- только человекочитаемые market/event вопросы;
- не брать platform_meta, внутренние вопросы, machine fragments, parlays, player props с нулевым объёмом.

## AITestArena — текущее состояние после reset
Текущий активный раунд:
- round_id: `short-horizon-round-001`
- status: `open`
- cards_count: `5`
- cards_url: `https://aitestarena.com/rounds/short-horizon-round-001/cards.json`
- submit_endpoint: `https://aitestarena.com/api/rounds/short-horizon-round-001/answers/submit`
- source_policy: `owner_approved_external_sports_odds_candidates_only_no_internal_questions`

Текущие 5 карт Round 001:
1. `short-001-01-hurricanes-beat-canadiens-may22` — Will the Carolina Hurricanes beat the Montreal Canadiens?
2. `short-001-02-cavaliers-beat-knicks-may23` — Will the Cleveland Cavaliers beat the New York Knicks?
3. `short-001-03-knicks-cavaliers-total-over-215-5` — Will total points in Knicks vs Cavaliers be over 215.5?
4. `short-001-04-avalanche-beat-golden-knights-may25` — Will the Colorado Avalanche beat the Vegas Golden Knights?
5. `short-001-05-hurricanes-beat-canadiens-may27` — Will the Carolina Hurricanes beat the Montreal Canadiens on May 27?

## AITestArena — что было исправлено
1. Старые public refs Round 002 / Round 003 были убраны из активных публичных поверхностей.
2. Round 003 meta-only был закрыт как ошибка. Текущий round был reset к fresh Round 001.
3. Был создан outcome template: `/root/aitestarena/state/round001_outcomes.json`. Сейчас status: `pending_settlement`, `outcome_yes=null` для всех 5 карт.
4. Был создан scorer v1: `/root/aitestarena/state/round001_scores.json`. Публичная страница leaderboard обновляется из scorer. Сейчас: `pending_settlement`, `settled_cards=0/5`, `submissions_non_smoke=0`.
5. Submit API сначала падал с `canonical_cards_unavailable`. Была пропатчена функция `load_canonical_cards` в `/root/aitestarena/server/aitestarena__short_round_answer_server.py`. Теперь canonical fallback читает live cards из `/var/www/aitestarena/rounds/<round_id>/cards.json`.
6. Smoke submit после patch прошёл: HTTP 200, `answers_count=5`, `round_id=short-horizon-round-001`, `status=submitted_pending_resolution`, `total_virtual_allocation=0`.
7. Agent Cabinet frontend был восстановлен из backup, потому что reset перезаписал его заглушкой. Файл снова около 51 KB и содержит token/API/profile/readiness логику.

## AITestArena — что ещё не завершено / где риск
1. Главная и часть фронта были повреждены грубым reset. Нужно восстановить нормальную витрину точечно, не трогая Round 001 / submit API / scorer.
2. Cabinet восстановлен, но после restore в нём оставались старые Round 002 тексты и internal-вопросы. Нужно дочистить только cabinet content refs до Round 001 sports/odds, не трогая auth JS.
3. Leaderboard на мобильном экране уезжал из-за широкой таблицы. Нужно добавить горизонтальный wrapper/overflow, не меняя scoring logic.
4. Нельзя больше запускать большие reset-скрипты по фронту без read-only проверки backup и точечного плана.

## FirstMeet growth / outreach — что обнаружено
Почта спамила письмами:
`FirstMeet: нужен добор лидов — GROWTH/ACTION — 2026-05-20`

Письма приходили примерно каждые 30 минут.

Read-only диагностика показала:
- `/etc/cron.d/firstmeet_outreach_health` запускает health watcher каждые 30 минут с 04–17 UTC.
- `/root/firstmeet_growth/logs/outreach_due_send.log` содержит повторяющиеся ошибки: `ERROR: lead not found in queue: <lead_id>`.
- `/root/firstmeet_growth/state/outreach_schedule.csv` содержит open-like строки со статусами `scheduled`/`sending`, часть из них битая.
- Лиды в `leads_master` есть: `new=51`, `ready_to_prepare=49`, `cabinet_created=24`, `sent=210`, `hard_bounce=2`.

Вывод: проблема не только в оповещениях. Outreach pipeline имеет битую связку schedule ↔ queue/leads, а watcher повторяет один и тот же WARN письмами.

## FirstMeet growth — безопасный план продолжения
Не глушить transactional FirstMeet email. Не трогать обычные формы/кабинеты/платежи.

Порядок на следующий сеанс:
1. Остановить почтовый спам health-alert: перевести `firstmeet_outreach_health` на один запуск в день или добавить daily lock/dedupe.
2. Аккуратно почистить/пометить битые `scheduled`/`sending` строки в `outreach_schedule.csv` с backup.
3. Проверить build queue → prepare cabinets → schedule sends.
4. Запустить guarded dry-run / prepare cycle без массовой отправки.
5. Убедиться, что `send_due_outreach_email.py` больше не пишет `lead not found in queue`.
6. Только после этого считать конвейер восстановленным.

## Важные backup / файлы, упомянутые в сессии
AITestArena:
- `/root/aitestarena/backups/reset_to_fresh_round001_20260520_101357/`
- `/root/aitestarena/server/aitestarena__short_round_answer_server.py.bak.canonical_fallback_20260520_113524`
- `/var/www/aitestarena/rounds/short-horizon-round-001/cards.json`
- `/root/aitestarena/state/round001_outcomes.json`
- `/root/aitestarena/state/round001_scores.json`
- `/root/aitestarena/logs/short_round_submit_8098.log`

FirstMeet growth:
- `/root/firstmeet_growth/leads/leads_master.csv`
- `/root/firstmeet_growth/state/outreach_schedule.csv`
- `/root/firstmeet_growth/logs/outreach_due_send.log`
- `/root/firstmeet_growth/logs/outreach_health.log`
- `/etc/cron.d/firstmeet_outreach_health`
- `/etc/cron.d/firstmeet_outreach_randomized`

## Рабочее правило на будущее
Перед любым изменением:
- read-only проверка;
- точный файл;
- backup;
- минимальный patch;
- проверка;
- rollback path.

Не запускать широкие reset-скрипты, которые переписывают несколько HTML/API/state слоёв сразу.

## Что не было сохранено
Секреты, SMTP passwords, API keys, private cabinet tokens и персональные приватные данные не сохранялись.
