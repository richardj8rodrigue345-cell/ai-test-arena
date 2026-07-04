# PUBLISH GATE PROTOCOL — @psihiatriya_legko

## Single Source of Truth

Publish-gate имеет ровно одно состояние на каждый publish-пакет. Состояние хранится в `publish_packages/<name>/GATE_STATE.md`.

Состояния:
- `READY_TO_PUBLISH` — пакет approved, все сигналы согласованы, можно публиковать
- `BLOCKED_NEEDS_EDIT` — требуется редактура, owner ещё не approved
- `BLOCKED_DO_NOT_PUBLISH` — owner явно запретил публикацию
- `BLOCKED_CONTRADICTORY_APPROVAL_STATE` — approval.md и review.md противоречат друг другу
- `PUBLISHED` — пост опубликован, msg_id записан
- `FAILED` — попытка публикации была, но не удалась (ошибка Telegram, скрипта и т.д.)

## Atomic Owner Approval

Когда owner утверждает пакет, оператор ОБЯЗАН привести ВСЕ файлы пакета к согласованному состоянию:

```
GATE_STATE.md:     READY_TO_PUBLISH
approval.md:       PUBLISH_APPROVED: true
review.md:         PUBLISH_APPROVED: true, DO_NOT_PUBLISH: false
card_status.md:    DO_NOT_PUBLISH: false
```

**Запрещено:** оставлять `DO_NOT_PUBLISH: true` рядом с `PUBLISH_APPROVED: true` в любом файле пакета.

## Pre-flight Gate (перед каждой публикацией)

Перед вызовом publish-скрипта ОБЯЗАТЕЛЬНА проверка:

1. `GATE_STATE.md` существует и содержит `READY_TO_PUBLISH`?
   - Нет → `BLOCKED: <причина>`, выход. Не тратить время на генерацию.
2. `approval.md`: `PUBLISH_APPROVED: true`?
   - Нет → `BLOCKED_DO_NOT_PUBLISH`
3. `review.md`: `DO_NOT_PUBLISH: false`?
   - `true` → `BLOCKED_CONTRADICTORY_APPROVAL_STATE`
4. `post.md` или `post_draft.md` существует и не пуст?
   - Нет → `BLOCKED_NO_APPROVED_DRAFT`
5. `card.png` существует? (только для photo-режимов)
   - Если нужна карточка и нет → `BLOCKED_NO_CARD`

Все 5 условий выполнены → `READY_TO_PUBLISH` → можно вызывать publish-скрипт.

## Scheduled Cron Protocol (ПН-ЧТ-СБ 12:00 МСК)

Cron НЕ занимается генерацией контента. Только publish:

```
1. PRE-FLIGHT
   → Проверить publish_packages/ на наличие approved пакета
   → Выполнить pre-flight gate (5 условий)
   → Если BLOCKED → записать причину, выход со статусом BLOCKED_<reason>
   → Если READY → продолжить

2. PREPARE
   → Скопировать post_draft.md → _post_draft.md
   → Если есть card.png в пакете → скопировать в card.png
   → Проверить длину текста (≤1024 для photo_caption, иначе photo_then_text)

3. DRY-RUN
   → Вызвать publish_card_to_psihiatriya.py --dry-run
   → Проверить: can_post_messages=true, would_send_photo=true
   → Если dry-run FAIL → FAIL: DRY_RUN_FAILED, выход

4. PUBLISH
   → Вызвать publish_card_to_psihiatriya.py (без --dry-run)
   → Записать: telegram_send_attempted=true
   → Если скрипт НЕ БЫЛ ВЫЗВАН → FAIL: PUBLISH_SCRIPT_NOT_INVOKED
   → Получить message_id из вывода скрипта

5. VERIFY
   → Проверить: новый пост в t.me/s/psihiatriya_legko?
   → Проверить: новый msg_id в publication_links.md?
   → Записать в publish_tracking:
     - telegram_send_attempted: true
     - telegram_send_ok: true/false
     - telegram_msg_id: <id>
     - publication_links_updated: true/false
     - postflight_verified: true/false

6. UPDATE GATE
   → GATE_STATE.md = PUBLISHED
```

## Publish Tracking Fields (независимо от lastDelivered)

Файл: `outbox/publish_tracking.jsonl`

Каждая попытка публикации записывает строку:
```json
{
  "ts": "ISO8601",
  "slot": "ЧТ 02.07 12:00 МСК",
  "package": "publish_packages/planning_20260701",
  "gate_state": "READY_TO_PUBLISH",
  "telegram_send_attempted": true,
  "telegram_send_ok": true,
  "telegram_msg_id": 474,
  "publication_links_updated": true,
  "postflight_verified": true,
  "status": "PUBLISHED"
}
```

`lastDelivered` из cron-фреймворка НЕ используется как признак публикации. Это поле про анонс cron-задачи, не про Telegram-доставку поста.

## Failure Modes

| Status | Trigger | Action |
|--------|---------|--------|
| `BLOCKED_NEEDS_EDIT` | review.md: DO_NOT_PUBLISH=true, нет approval | Не тратить время. Ждать правок + approval. |
| `BLOCKED_DO_NOT_PUBLISH` | owner явно запретил | Не публиковать. |
| `BLOCKED_CONTRADICTORY_APPROVAL_STATE` | approval=YES + review/card_status=NO | Немедленно сообщить. Не публиковать. |
| `BLOCKED_NO_APPROVED_DRAFT` | Нет post.md / post_draft.md | Создать draft → review → approval → publish. |
| `BLOCKED_NO_CARD` | Нет card.png для photo-режима | Сгенерировать карточку. |
| `FAIL: PUBLISH_SCRIPT_NOT_INVOKED` | publish_card_to_psihiatriya.py не вызван | Root-cause: почему агент не дошёл до publish? |
| `FAIL: DRY_RUN_FAILED` | dry-run вернул ошибку | Проверить вывод dry-run. |
| `FAILED` | Скрипт вызван, но Telegram вернул ошибку | Записать в publish_errors.log. |
| `FAIL: POSTFLIGHT_MISMATCH` | Пост опубликован, но не найден в канале/links | Ручная проверка. |
