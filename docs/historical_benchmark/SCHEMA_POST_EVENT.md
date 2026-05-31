# Schema: Post-event Layer

Purpose: store results and settlement data available only after the event.

This layer is evaluator-only and must never be agent input.

## Required fields

- `layer`: must be `post_event`
- `record_type`
- `source`
- `event_id`
- `game_date` or `settled_at`
- `home_team`
- `away_team`
- `settlement_source`
- `not_for_agent_input`: must be `true`
- `not_for_live_decision_use`: must be `true`

## Optional fields

- `points`
- `win_margin`
- `home_score`
- `away_score`
- `result_home_moneyline`
- `result_away_moneyline`
- `actual_margin`
- `actual_total`
- `closing_odds`
- `clv`

## Forbidden fields

The post-event layer must not contain:

- future recommendations
- future picks
- live ENTER / WAIT / SKIP directives
- `agent_decisions.csv` write instructions
- live bankroll updates
- current watchlist mutation instructions

## Example

```json
{"layer":"post_event","record_type":"historical_game_result","source":"kyleskom/NBA-Machine-Learning-Sports-Betting","event_id":"nba_2007-01-02_orlando_magic_new_jersey_nets","game_date":"2007-01-02","home_team":"Orlando Magic","away_team":"New Jersey Nets","points":191,"win_margin":-1,"result_home_moneyline":"LOSS","result_away_moneyline":"WIN","settlement_source":"kyleskom/OddsData.sqlite","not_for_agent_input":true,"not_for_live_decision_use":true}
```

## Validation rules

1. `event_id` must match a pre-event record.
2. `not_for_agent_input` must be true.
3. `not_for_live_decision_use` must be true.
4. Post-event data may be read only by evaluator logic.
5. Post-event data must never be provided to historical decision generation.
