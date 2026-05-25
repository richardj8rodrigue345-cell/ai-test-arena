# BOOT CONTEXT FOR CHATGPT — AITestArena / OpenClaw / FirstMeet

### 1. Current source-of-truth
Приоритет определения активного состояния системы (Active Truth):
1.  **`docs/ops/aitestarena-paper-agent-cycle-results-2026-05-24.md`** — главный компактный операционный источник для восстановления контекста.
2.  Текущие cron-файлы, особенно **`ops/cron/root_aitestarena_hourly_cycle_outer_guard.cron`**.
3.  Текущие файлы `AGENTS.md` и `HEARTBEAT.md`.
4.  Live server check / фактический вывод команд в текущей сессии.
5.  Project profiles — только справочный слой; при конфликте с вышеуказанными пунктами считаются устаревшими.

### 2. Role boundaries
*   **Writer:** Создает контент для канала «Психиатрия легко» и AI-комментарии для FirstMeet. **Строго запрещено:** писать код, отправлять терминальные команды, изменять файлы Арены, банкроллы или решения агентов.
*   **Stalker / Decision layer:** Может записывать только «бумажные» (paper-only) решения **ENTER / WAIT / SKIP** в файл `agent_decisions.csv`.
*   **Sentinel:** Наблюдатель в режиме read-only. Сообщает статус OK/WARN/FAIL. **Запрещено:** вносить любые изменения в систему, файлы, писать код или принимать решения в Арене.
*   **Важное ограничение:** Writer и Sentinel никогда не должны касаться `agent_decisions`, банкролла, расчетов (settlement) или состояния watchlist.

### 3. AITestArena active cycle
*   **02 wake Stalker:** Ежечасный поиск событий и подготовка кандидатов.
*   **07 paper-agent wrapper (активные шаги):**
    1.  `deepseek_safe_runner` (применение решений).
    2.  `settlement` (расчет исходов).
    3.  `recount_enter_voids` (пересчет возвратов).
    4.  `agent_results_analysis` (анализ статистики).
    5.  `render` (генерация страниц).
    6.  **`CYCLE_DONE`**.
*   **Public pipeline (`12,32,52`):** Обновляет публичную витрину (vitrina).
*   **Mini Scout internal pipeline (`14,34,54`):** Формирует внутренний шорт-лист и JSON для входа GPT.
*   **Final identity guard:** Находится **ВНЕ wrapper**, в файле `ops/cron/root_aitestarena_hourly_cycle_outer_guard.cron`. Запускает `enforce_mini_scout_identity.py` после полного завершения wrapper для восстановления имен и банкролла (1000).

### 4. Paper betting / bankroll rules
*   Все операции — **100% виртуальные кредиты (paper-only)**. Реальные деньги и азартные игры запрещены.
*   **`settle_agent_positions_from_watchlist.py`:** Официальный инструмент расчета исходов. **НЕ является read-only**: он закрывает позиции, переносит записи из open в settled и обновляет банкролл.
*   **`analyze_agent_paper_results.py`:** Работает строго в режиме **read-only**. Он читает данные и пишет отчеты, но не имеет права изменять банкролл или историю.
*   **Запреты:** Любые ручные правки банкролла, истории или позиций строго запрещены. Изменение банкролла допустимо только через официальный settlement/process пайплайн.

### 5. Public pages histories
*   На странице `/agents/` должны быть видны исполненные ставки как **«История paper-ставок / Settled paper history»**.
*   Публичные данные истории экспортируются в `data/agents/<agent_id>/history.json`.
*   Внутренний источник истории — `/root/aitestarena/agents/<agent_id>/positions_settled.jsonl`.

### 6. Save / commit / NotebookLM protocol
*   После любого `save` или `commit` необходимо проверять целостность идентичности агентов и ролей.
*   При обнаружении **CONTEXT CONFLICT** — немедленно сообщать пользователю, отдавая приоритет операционным документам и крону.

### 7. Mistakes not to repeat
*   Не переименовывать `agent_id=gpt-mini` (связь с историей).
*   Не позволять Writer давать код или терминальные команды.
*   Не считать Brier score подтвержденным (в коде анализатора подтверждены только PnL и счетчики).
*   Не путать: **settlement** меняет данные, **analysis** только читает их.

### 8. First action rule for ChatGPT
Перед любой bash-командой или patch ассистент обязан сначала написать:
«Восстановил контур:
*   **Writer** = psychology channel + FirstMeet AI comments, not AITestArena.
*   **Stalker / decision layer** = paper-only ENTER-WAIT-SKIP.
*   **Sentinel** = read-only OK/WARN/FAIL.
*   **07-cycle wrapper** = runner → settlement (write) → recount → analysis (read) → render → CYCLE_DONE.
*   **Final identity guard** = outer cron, not EXIT trap.
*   **Expected impact of this action:** [описание влияния]»

### 9. Source maintenance / где сохранять изменения и как часто обновлять
1.  **Главный актуальный источник:** `docs/ops/aitestarena-paper-agent-cycle-results-2026-05-24.md`. Здесь сохранять краткое описание изменений крона, цикла, границ ролей, инвариантов страниц и логики расчетов.
2.  **GitHub:** После каждой важной серверной правки коммитить изменения в репозиторий `richardj8rodrigue345-cell/ai-test-arena`. Сохранять: скрипты, `AGENTS.md`, `HEARTBEAT.md`, файлы `.cron` и `docs/ops/*.md`.
3.  **Google Drive / CURRENT STATE:** Сохранять короткий human-readable update (что изменилось, commit SHA, какие проверки прошли, что является active source).
4.  **NotebookLM:** После каждого важного commit/update:
    *   Обновить context pack.
    *   Заменить источник в NotebookLM.
    *   Задать проверку `ACTIVE CONTEXT CHECK`.
    *   Принять сохранение только при ответе `CONTEXT OK`.
5.  **Частота обновлений:**
    *   Сразу после важных правок сервера/GitHub/cron.
    *   Минимум в конце каждой рабочей сессии при изменении контура.
6.  **Что не сохранять:** Терминальные дампы, failed attempts, backup-файлы, секреты/ключи, приватные данные FirstMeet.
7.  **Обязательный post-save check:** После save/commit ChatGPT должен запросить у NotebookLM проверку:
    *   “Проверь свежий ACTIVE CONTEXT после последнего update. Есть ли противоречия? Final guard всё ещё outer cron? Writer всё ещё not AITestArena? Analysis всё ещё read-only? Settlement всё ещё official write step? Histories всё ещё visible on /agents/? Ответь CONTEXT OK или CONTEXT CONFLICT.”
8.  **При CONTEXT CONFLICT:** Остановить изменения, найти конфликтующий источник, исправить его в GitHub/docs, обновить NotebookLM и повторить проверку.

**CONTEXT OK**
