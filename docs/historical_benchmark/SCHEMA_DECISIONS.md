# Schema: Historical Decision Layer

Purpose: store historical strategy or agent actions created from pre-event data only.

This layer is separate from live AITestArena decisions.

## Terminology guard

Live AITestArena uses `ENTER`, `WAIT`, `SKIP` in `agent_decisions.csv`.

Historical benchmark must use separate action terms:

- `PICK`
- `PASS`
- `NO_DATA`
- `VOID`
- `BASELINE_PICK`

Historical actions are not live ENTER / WAIT / SKIP and must never be written to `agent_decisions.csv`.

## Required fields

- `decision_id`
- `event_id`
- `source_strategy`
- `decision_timestamp_utc` or `decision_replay_at`
- `historical_action`
- `market`
- `selection`
- `odds_at_decision`
- `stake_units`
- `not_for_live_decision_use`: must be `true`
- `does_not_write_to_agent_decisions_csv`: must be `true`

## Optional fields

- `predicted_probability`
- `predicted_edge`
- `confidence`
- `kelly_fraction`
- `reason`
- `input_snapshot_id`

## Forbidden fields

- final score
- points
- win margin
- result
- settlement outcome
- PnL
- CLV
- post-event notes
- live bankroll instructions
- future live recommendations

## Example

```json
{"decision_id":"hist_decision_nba_2007-01-02_orlando_magic_new_jersey_nets_home_ml","event_id":"nba_2007-01-02_orlando_magic_new_jersey_nets","source_strategy":"baseline_home_moneyline","historical_action":"BASELINE_PICK","market":"moneyline","selection":"home","odds_at_decision":1.385,"stake_units":1.0,"not_for_live_decision_use":true,"does_not_write_to_agent_decisions_csv":true}
```

## Validation rules

1. `event_id` must exist in pre-event layer.
2. Historical decision creation must not read post-event layer.
3. `not_for_live_decision_use` must be true.
4. `does_not_write_to_agent_decisions_csv` must be true.
5. Negative-edge mechanical baselines are allowed only as historical baseline simulations, not as live AITestArena decisions.
