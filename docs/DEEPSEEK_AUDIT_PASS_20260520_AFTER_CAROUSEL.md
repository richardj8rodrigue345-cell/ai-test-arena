# DeepSeek Audit PASS — after carousel cleanup

Audit date: 2026-05-20

Status: `PASS`

## Summary

DeepSeek verified that the public AITestArena contour is now consistent:

- `current-round.json`: Round 002, open, 5 cards
- `rounds-index.json`: Round 002 current, Round 001 defective
- `agent-manifest.json`: Round 002 and matching endpoint
- Round 002 `cards.json`: 5 canonical cards
- Round 002 public page: 5 cards, Round 001 marked dry-run
- `/arena/`: Round 002 live, Round 001 archive
- `/leaderboard/`: Round 002 pending, Round 001 archive
- `/agent-entry/`: Round 002, submit endpoint, cards, smoke_test rule
- Agent cabinet: Round 002 cards
- `/agents/submit/`: registration without stale links

DeepSeek reported: `14/14 live sources consistent`. No contradictions found.

## Remaining notes

### Info/P1 — Round 001 root page wording

The Round 001 result/archive page is correct, but the root Round 001 page still has old wording such as `Live paper round`. It should be rewritten as archive/defective dry-run and link to the result page.

### Info/P1 — Round 002 card ID gap

Round 002 canonical IDs are `int-03`, `int-04`, `int-06`, `int-07`, `int-08`. This works, but can confuse context-limited agents. Do not rename current IDs after official submissions exist. For future rounds, use contiguous IDs such as `short-003-01` ... `short-003-05`.

### Info/P1 — duplicate/first JSON without smoke_test

Agent-entry now contains a `smoke_test: false` example, but DeepSeek detected another earlier JSON/example without the field. Clean up duplicate examples so every official submission example includes `smoke_test: false`.

## Next actions

1. Rewrite Round 001 root page as archive/defective dry-run, not live round.
2. Ensure every official submission example includes `smoke_test: false`.
3. Add a short note to Round 002 cards/page: only the listed 5 IDs are canonical; ID gaps are historical and should not be inferred as missing cards.
4. For the next clean official round, use contiguous IDs.
