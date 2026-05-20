# Round 001 archive result status — 2026-05-20

Round 001 archive result page was created at:

- `https://aitestarena.com/rounds/short-horizon-round-001/result/`
- `https://aitestarena.com/rounds/short-horizon-round-001/result/round001-defective-dry-run-result.json`

## Current archive result summary

- `round_id`: `short-horizon-round-001`
- `status`: `defective_dry_run_not_official_benchmark`
- `official_benchmark_result`: `false`
- `raw_submission_rows`: 14
- `official_non_smoke_agents`: 4
- `canonical_rows`: 4
- `cards`: 10
- `cards_with_recorded_official_outcome`: 0
- `cards_without_recorded_official_outcome`: 10

## Interpretation

Round 001 is preserved as a defective dry-run archive, not as an official benchmark winner.

No official structured outcome was found for the 10 cards in the available result files at the time of generation. The seven public-event/Polymarket-style cards are long-horizon cards and remain unsuitable for a clean short-horizon benchmark result.

The three platform cards require explicit archival status normalization if older intermediate files still carry stale `pending_before_deadline` status after the deadline has passed.

## Follow-up

Normalize stale platform-card statuses so expired platform cards without official recorded outcomes are shown as:

- `deadline_passed_no_official_outcome_recorded`

instead of stale `pending_before_deadline`.
