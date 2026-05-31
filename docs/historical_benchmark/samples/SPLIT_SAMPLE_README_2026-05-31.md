# Split Sample README — kyleskom OddsData

Date: 2026-05-31.

Source: kyleskom/NBA-Machine-Learning-Sports-Betting (`OddsData.sqlite`).

Purpose: demonstrate pre-event / post-event data split for historical benchmark.

## Files

- `pre_event_sample_kyleskom_2026-05-31.jsonl`
- `post_event_sample_kyleskom_2026-05-31.jsonl`

## Verification from server run

- pre_count = 20
- post_count = 20
- event_ids_match = true
- no forbidden fields in pre_event
- pre_event `result_known=false`
- all rows `not_for_live_decision_use=true`
- post_event `not_for_agent_input=true`

## Timestamp quality

The kyleskom dataset does not record exact pick timestamps, only game dates.

Use:

- `timestamp_quality=weak`
- `data_cutoff_status=game_date_only_no_pick_timestamp`

## Safety

This sample is historical benchmark material only.

It is not used for live AITestArena ENTER/WAIT/SKIP, not written to `agent_decisions.csv`, and not referenced by the live watchlist outbox.
