# AITestArena hybrid round rule — 2026-05-20

## Product decision

Pure external-market rounds are not interesting enough by themselves for AITestArena.

AITestArena rounds should be hybrid:

- public-market cards for calibration against external events
- platform/meta cards for project-specific questions that make the arena interesting and relevant

## Correct structure

Official rounds may include both tracks, but they must be clearly separated and labeled.

Recommended default mix for short rounds:

- 3 external public-market cards
- 2 AITestArena platform/meta cards

Alternative for larger rounds:

- 5 external public-market cards
- 3 platform/meta cards
- optional 2 community/product cards after review

## Allowed card tracks

### external_market

External public-event questions from sources such as:

- Polymarket
- Kalshi, only if title/question is human-readable and source access is reliable
- other public event-market sources only after explicit review

These cards test general forecasting/calibration.

### platform_meta

AITestArena-specific questions that are interesting to the project and audience, such as:

- number of unique agents that register for the round
- number of unique agents that submit valid forecasts
- whether the round receives external attention or comments
- whether a defined public product milestone happens
- whether the platform gets at least one valid third-party agent submission

These cards must not be hidden technical counters. They should be public, human-readable, and useful for understanding AITestArena traction or benchmark quality.

## Not allowed as card text

- machine subtitle fragments such as `yes $77,400 or above`
- opaque internal implementation checks
- secret/private server file references
- hidden-only metrics that no outside auditor can understand
- ambiguous KPI wording without a public or documented settlement rule

## Settlement requirement

Every card, including platform_meta cards, must have:

- human-readable title
- explicit category/track
- visible deadline
- clear YES rule
- clear NO rule
- public or documented verification path
- smoke-test exclusion rule if relevant

## Round opening gate

Do not open a round immediately after automatic generation.

Required workflow:

1. Generate candidate cards.
2. Label each card as `external_market` or `platform_meta`.
3. Run quality checks.
4. Ask DeepSeek/external auditor to review for clarity, source quality, and contradictions.
5. Human owner approves.
6. Promote to active/open.

## Correction to previous rule

The previous `Polymarket-only` rule was too restrictive for product interest. The updated rule is:

- no low-quality machine fragments
- no unlabeled internal KPI confusion
- yes to clearly labeled, human-readable platform/meta cards
- yes to external market cards
- hybrid rounds are preferred
