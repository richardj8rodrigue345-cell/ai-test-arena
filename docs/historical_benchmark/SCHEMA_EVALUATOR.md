# Schema: Historical Evaluator Layer

Purpose: join historical decisions with post-event outcomes and compute metrics.

This layer is deterministic and evaluator-only.

## Required fields

- `evaluation_id`
- `decision_id`
- `event_id`
- `source_strategy`
- `result`
- `stake_units`
- `pnl_units`
- `not_for_agent_input`: must be `true`
- `not_for_live_decision_use`: must be `true`
- `does_not_write_to_live_bankroll`: must be `true`

## Optional fields

- `odds_at_decision`
- `closing_odds`
- `clv`
- `roi`
- `market`
- `selection`
- `actual_margin`
- `actual_total`
- `evaluator_version`

## Forbidden fields

- live bankroll references
- next bet size recommendation
- future predictions
- live ENTER / WAIT / SKIP directives
- live watchlist mutation instructions

## PnL rules

For decimal odds:

- WIN: `pnl_units = stake_units * (odds_at_decision - 1)`
- LOSS: `pnl_units = -stake_units`
- VOID/PUSH: `pnl_units = 0`

## Example

```json
{"evaluation_id":"hist_decision_nba_2007-01-02_orlando_magic_new_jersey_nets_home_ml_eval","decision_id":"hist_decision_nba_2007-01-02_orlando_magic_new_jersey_nets_home_ml","event_id":"nba_2007-01-02_orlando_magic_new_jersey_nets","source_strategy":"baseline_home_moneyline","result":"LOSS","stake_units":1.0,"odds_at_decision":1.385,"pnl_units":-1.0,"roi":-1.0,"not_for_agent_input":true,"not_for_live_decision_use":true,"does_not_write_to_live_bankroll":true}
```

## Validation rules

1. `decision_id` must exist in historical decision layer.
2. `event_id` must exist in post-event layer.
3. Evaluator must not write to live bankroll.
4. Evaluator must not write to `agent_decisions.csv`.
5. Evaluator must not generate future recommendations.
