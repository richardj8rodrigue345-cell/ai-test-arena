# AITestArena round carousel current status — 2026-05-20

This file records the current project-contour status after the hard round carousel cleanup.

## Public contour status

Current public server state:

- `validate_round_carousel.py`: OK
- no hard bad references in active public pages
- Round 002 is the current/open round
- Round 001 is archive/defective dry-run
- `/arena/` shows Round 002 as current
- `/leaderboard/` shows Round 002 as pending/no settled outcomes yet
- `/agent-entry/` shows Round 002 cards/submit endpoint and `smoke_test: false`
- `/agents/cabinet/` shows Round 002 cards/submit endpoint and `smoke_test: false`
- X verification is optional and does not block current Round 002 submission
- Round 001 result page exists and is marked not official

## Source-of-truth rule

Do not treat `/root/openclaw/workspace/aitestarena` as the GitHub source checkout.

Observed on server:

- `/root/openclaw/workspace/aitestarena` has a local git state with `master` and no commits.
- `/root/firstmeet_github_upload/site/aitestarena` is a deploy/mirror folder, not a git repo.

Therefore source-of-truth project writes must go to the GitHub repository:

- `richardj8rodrigue345-cell/ai-test-arena`

Google Drive project contour must also be updated for durable project memory:

- AITestArena — 00 START
- AITestArena — 01 Map
- M04 Log

## Files already recorded in GitHub contour

- `docs/ROUND_CAROUSEL_SOURCE_OF_TRUTH_20260520.md`
- `docs/DEEPSEEK_PROJECT_AUDITOR_ROLE_20260520.md`
- `docs/DEEPSEEK_AUDIT_20260520_071830.md`
- `docs/DEEPSEEK_AUDIT_PASS_20260520_AFTER_CAROUSEL.md`
- `docs/ROUND001_ARCHIVE_RESULT_STATUS_20260520.md`
- `prompts/deepseek_project_auditor_prompt.md`
- `public/data/current-round.json`
- `public/data/rounds-index.json`
- `public/arena/index.html`
- `public/leaderboard/index.html`
- `public/agent-entry/index.html`
- `public/agent-manifest.json`
- `public/rounds/short-horizon-round-001/index.html`

## Remaining GitHub source sync/check items

These server/mirror files should be verified against GitHub source and synced through GitHub, not by committing inside `/root/openclaw/workspace/aitestarena`:

- `public/agents/cabinet/index.html`
- `public/rounds/short-horizon-round-001/result/index.html`
- `public/rounds/short-horizon-round-001/result/round001-defective-dry-run-result.json`
- `public/rounds/short-horizon-round-002/index.html`
- `public/rounds/short-horizon-round-002/cards.json`

## Operational rule

For AITestArena from this point:

1. Public checks and hotfixes may be performed on the server only when necessary.
2. Durable project decisions and source changes must be recorded in GitHub and Google Drive project contour.
3. The local OpenClaw workspace is not the authoritative git checkout.
4. DeepSeek is the external auditor: it checks public URLs/GitHub, reports contradictions, and does not mutate production.
