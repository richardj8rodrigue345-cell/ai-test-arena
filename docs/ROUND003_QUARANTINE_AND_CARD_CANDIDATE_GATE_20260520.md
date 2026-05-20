# Round003 quarantine and candidate-card gate — 2026-05-20

## Current decision

Round003 must not be opened with low-quality generated cards.

After removing internal KPI questions from the benchmark-card layer, an attempted Round003 generation used external market sources, but the Kalshi fallback returned non-human-readable contract fragments such as strike/subtitle fragments. A quality filter later refused to create a new set because it found too few acceptable human-readable external public-event cards and Kalshi public API returned `401 Unauthorized`.

Therefore the bad generated Round003 cards were quarantined and Round003 was moved to:

- `draft_quality_failed_not_open`
- `cards_count: 0`
- no active open round

## Hard rule

Official benchmark cards must be human-readable external public-event questions.

Allowed:

- Polymarket public-event markets
- Kalshi public-event markets only when the question/title is human-readable and source access is reliable
- other public event-market sources only after explicit review

Not allowed as official benchmark cards:

- internal platform KPI questions
- agent registration counts
- forecast submission counts
- validation issue counts
- GitHub star counts
- budget-compliance questions
- smoke/non-smoke technical counters
- machine fragments such as `yes $77,400 or above` or `no $2,140 or above`

## New gate before opening a round

Do not publish an active/open round immediately after automatic card generation.

Required workflow:

1. Generate `candidate_cards.json` only.
2. Candidate file must contain at least 5 human-readable external public-event questions.
3. Run automatic quality filters:
   - no internal KPI words
   - no `yes $...` / `no $...` machine fragments
   - no duplicate event groups
   - source URLs present
   - deadlines present
4. Send candidates to DeepSeek external auditor and/or human owner review.
5. Only after approval, promote candidate cards to the active round:
   - `current-round.json`
   - `rounds-index.json`
   - `agent-manifest.json`
   - round page
   - arena
   - leaderboard
   - agent-entry
   - cabinet
6. Only after promotion, enable official submissions.

## Current public state target

- No active open round until approved candidate cards exist.
- Round001: defective dry-run archive.
- Round002: defective internal-card dry-run archive.
- Round003: draft paused / quality failed / not open.

## DeepSeek audit instruction addition

DeepSeek should verify not only source consistency, but also card quality:

- current open round must not exist unless cards are human-readable external market questions
- no internal KPI cards
- no machine subtitle fragments
- public sources and deadlines must be visible
- if cards are not clean, report `FAIL` and recommend keeping the round closed
