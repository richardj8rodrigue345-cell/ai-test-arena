TASK_ID: WRITER-STALKER-20260704-001
TARGET_AGENT: STALKER
STATUS: REQUESTED
CREATED_AT: 2026-07-04 09:21 CEST
DEADLINE: 2026-07-05 12:00 CEST
REQUESTED_BY: Writer
OWNER_REVIEW_REQUIRED: true
WRITER_ACK_REQUIRED: true

---

TOPIC:
Конкурентный бенчмаркинг — график публикаций 2–3 русскоязычных Telegram-каналов в нише психология / саморазвитие / ментальное здоровье.

Writer уже провёл внутренний анализ 20 постов @psihiatriya_legko (optimal_schedule_20260704.md). Выводы: золотое окно 14:00 CEST, лучшие дни ВС и СР, 1 пост в день — закон, ритм 2 раза в неделю с gap 3–4 дня.

Нужна внешняя проверка: совпадает ли этот паттерн с практикой похожих каналов или мы упускаем слот/день/частоту.

**Важно:** эта задача — не про Q5. Q5 уже packaged и ждёт owner approval к ближайшему слоту. Разведка нужна для проверки графика и очереди после Q5.

WHY:
Текущий график Writer (СР + СБ, 14:00 CEST) основан только на внутренних данных. Без внешнего бенчмарка есть риск:
- Пропустить сильный слот, который аудитория психологии использует, а мы — нет
- Не заметить, что похожие каналы выходят чаще и собирают охват за счёт частоты
- Зафиксировать субоптимальный ритм, который ограничит рост

AFFECTED_QUEUE_ITEMS:
- Q6 (СР 09.07 14:00)
- Q4 (СБ 12.07 14:00)
- Q_SURV (СР 16.07 14:00)
- Q9 (СБ 19.07 14:00)

Q5 исключён — уже packaged, ждёт owner approval.

SCOPE:
- Только публичные русскоязычные каналы и посты
- Без личных сообщений
- Без ручного контакта с владельцами каналов
- Без комментариев от нашего имени
- Без подписок / лайков / любых активных действий
- Только наблюдение и анализ публичных данных

SOURCE_FILES:
- publication_board: state/publication_board.md
- schedule report: reports/optimal_schedule_20260704.md
- style guide: constitution/STYLE_GUIDE_v1.md

STALKER_TASK:

Конкретный рейд, не общий scouting:

1. Найти 2–3 русскоязычных Telegram-канала в смежной нише (психология / саморазвитие / терапия / ментальное здоровье). Приоритет: каналы сопоставимого или чуть большего размера (200–2000 подписчиков), активные, публикующие регулярно. Только публичные каналы.

2. По каждому каналу зафиксировать последние 10–15 постов:
   - День недели публикации
   - Время публикации (CEST)
   - Интервал между постами (в днях)
   - Частота: сколько постов в неделю
   - Есть ли дни с 2+ постами

3. Сравнить с нашим графиком (optimal_schedule_20260704.md):
   - Совпадает ли наше «золотое окно» 14:00 с их практикой?
   - Используют ли они ВС — наш лучший день, но мы поставили СР+СБ?
   - Какая у них частота: чаще или реже наших 2 раз в неделю?
   - Видно ли, что частота коррелирует с ростом?

EXPECTED_OUTPUT:
Stalker должен вернуть:

signal: GREEN / YELLOW / RED

risk: LOW / MEDIUM / HIGH

divergence: где мы отклоняемся от практики похожих каналов (если отклоняемся)

examples: 2–3 конкретных наблюдения

recommendation: одно из —
- KEEP_SCHEDULE
- ADJUST_DAY
- ADJUST_TIME
- ADJUST_FREQUENCY
- HOLD_FOR_MORE_DATA

affected queue items: какие слоты затронуты

next action for Writer: что сделать с очередью

OUTPUT_PATH:
writer/outbox/stalker/BRIEF_WRITER-STALKER-20260704-001.md

WRITER_ACK_REQUIRED: true

---

TRANSITION_LOG:
DRAFT_FOR_OWNER_REVIEW → REQUESTED | 2026-07-04 09:30 CEST | Owner confirmed. Scope: public RU channels only, observation only, no contact, no comments, Q5 excluded. OUTPUT_PATH: writer/outbox/stalker/BRIEF_WRITER-STALKER-20260704-001.md. WRITER_ACK_REQUIRED: true.

STATUS: REQUESTED.
Stalker должен подхватить задачу и перевести в IN_PROGRESS. Controller проверяет переход DRAFT_FOR_OWNER_REVIEW → REQUESTED → IN_PROGRESS. Если через 6 часов нет IN_PROGRESS → WARN по Writer-Stalker Handoff Guard.
