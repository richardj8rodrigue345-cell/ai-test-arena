# Schema: Pre-event Layer

Purpose: store only information available before an event starts.

`not_for_live_decision_use` must always be `true`.

## Required fields

- `layer`: must be `pre_event`
- `record_type`
- `source`
- `source_role`
- `sport`
- `league`
- `event_id`
- `game_date` or `start_time_utc`
- `home_team`
- `away_team`
- `market`
- `selection`
- `odds_american` or `odds_decimal`
- `bookmaker_or_source`
- `timestamp_quality`
- `data_cutoff_status`
- `result_known`: must be `false`
- `not_for_live_decision_use`: must be `true`

## Optional fields

- `spread`
- `total_line`
- `prediction_created_at`
- `source_snapshot_at`
- `source_count`
- `data_quality`
- `leakage_risk`

## Forbidden fields

These fields must not appear in the pre-event layer:

- `points`
- `win_margin`
- `final_score`
- `home_score`
- `away_score`
- `result`
- `settlement`
- `profit`
- `pnl`
- `closing_odds`
- `clv`
- `actual_margin`
- `actual_total`
- `post_event`
- `outcome`

## Example

```json
{"layer":"pre_event","record_type":"historical_game_odds","source":"kyleskom/NBA-Machine-Learning-Sports-Betting","source_role":"historical_odds_results_dataset","sport":"basketball","league":"NBA","event_id":"nba_2007-01-02_orlando_magic_new_jersey_nets","game_date":"2007-01-02","home_team":"Orlando Magic","away_team":"New Jersey Nets","market":"moneyline","selection":"home","odds_american":-260,"odds_decimal":1.385,"spread":6.5,"total_line":199.5,"bookmaker_or_source":"SBR/kyleskom","timestamp_quality":"weak","data_cutoff_status":"game_date_only_no_pick_timestamp","result_known":false,"not_for_live_decision_use":true}
```

## Validation rules

1. `result_known` must be false.
2. `not_for_live_decision_use` must be true.
3. No forbidden fields may be present.
4. `event_id` must be stable and match the post-event layer.
5. If timestamp is only a game date, use `timestamp_quality=weak` and `data_cutoff_status=game_date_only_no_pick_timestamp`.
