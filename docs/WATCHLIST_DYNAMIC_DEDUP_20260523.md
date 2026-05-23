# AITestArena Watchlist dynamic data-only and dedup note — 2026-05-23

Status: applied and accepted for continuity.

## Summary

- Public Watchlist is now a stable dynamic shell: `/watchlist/` keeps the UI/CSS/fallback cards, but browser JS loads live review-cards from `/data/watchlist.json`.
- True data-only processor was created: `/root/aitestarena/tools/process_watchlist_outbox_data_only.py`.
- Guarded runner remains: `/root/aitestarena/tools/run_watchlist_data_only_guarded.sh`.
- UI/CSS render cron remains frozen. Do not re-enable old render cron without explicit owner approval.
- Mini is not enabled.
- No decision import, settlement, or bankroll mutation was run.
- Stalker added 12 fresh review-cards; `candidate_events.csv` reached 24 rows excluding header and `odds_snapshots.csv` reached 69 rows excluding header.
- Public JSON logic was changed so `NO_VALUE` stays visible as `NO_VALUE_REVIEW` when the event is valid. `NO_VALUE` means no value signal yet, not remove from Watchlist.
- Public Watchlist JSON intentionally excludes internal EV/Kelly/allocation/fair-probability fields.
- Full internal rows remain in `/root/aitestarena/watchlist/active`.
- Anti-duplicate rule accepted: `candidate_events.csv` stores unique review-cards; `odds_snapshots.csv` may store repeated line updates.

## Dedup rule

- `strict_key = event_id + market`.
- `semantic_key = sport + normalized_event + normalized_market + start_time_utc`.
- Same match + same market with different `event_id` is a duplicate.
- Same match + different market is a valid separate review-card.
- On duplicate: do not add a new `candidate_events.csv` row; add/update `odds_snapshots.csv` only.
- Current dataset after check: 24 candidate cards, no strict or semantic duplicates.

## Current public URLs

- Watchlist: https://aitestarena.com/watchlist/
- Machine JSON: https://aitestarena.com/data/watchlist.json

## Backups / rollback references

- `/root/aitestarena/backups/watchlist_dynamic_runtime_20260523-211236`
- `/root/aitestarena/backups/no_value_review_processor_20260523-212938`

## Next safe direction

- Keep public Watchlist as neutral review-card surface, not “best odds” page.
- Build the internal odds/value layer separately: implied probability, fair probability, EV, Kelly, confidence, line movement, second-source status.
- Public layer should show safe review-card fields only; internal value metrics stay hidden until appropriate settlement/audit views.
