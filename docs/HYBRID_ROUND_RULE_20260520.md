# AITestArena hybrid round rule — 2026-05-20

## Product decision

Pure external-market rounds are not interesting enough by themselves for AITestArena.

AITestArena rounds should be hybrid:

- public-market cards for calibration against external events
- platform/meta cards for project-specific questions that make the arena interesting and relevant

## Horizon rule

Short rounds must stay short.

Preferred horizon:

- 7 days when possible
- up to 10 days maximum for normal short rounds

Do not stretch short rounds to 30–90 days just to find more external-market cards. If only one or two good short external-market cards are available, keep fewer external cards and fill the rest with clearly labeled platform_meta cards, or keep the candidate in WARN/pending-review state.

The short-horizon feel is more important than forcing exactly 3 external cards.

## Correct structure

Official rounds may include both tracks, but they must be clearly separated and labeled.

Recommended default mix for short rounds:

- up to 3 external public-market cards if quality short-horizon cards exist
- 2–4 AITestArena platform/meta cards, depending on external-card availability
- 5 total cards after human/DeepSeek review

If fewer than 3 good external-market cards exist inside the 7–10 day window, do not lower quality or extend the horizon too far. Use fewer external cards or keep the round as candidate_pending_review.

Alternative for larger rounds:

- 5 external public-market cards
- 3 platform/meta cards
- optional 2 community/product cards after review

Larger rounds are separate from short rounds and must not silently replace short-round rules.

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
- short horizon stays short: 7 days preferred, 10 days maximum for normal short rounds
