# AITestArena pipeline split — public vitrina vs Mini Scout internal layer

Date: 2026-05-24

## Architecture

AITestArena now has three separated cron-driven layers.

### 1. Wake layer

Script:

`/root/aitestarena/tools/run_aitestarena_wake_stalker.sh`

Cron:

`2 * * * *`

Purpose:

Wake DeepSeek/Stalker through the existing bounded watchlist task.

### 2. Public vitrina layer

Script:

`/root/aitestarena/tools/run_aitestarena_public_pipeline.sh`

Cron:

`12,32,52 * * * *`

Purpose:

Process outbox CSV, update active watchlist data, and render the public watchlist/vitrina.

This layer may write the public vitrina.

It does not call GPT and does not write agent decisions.

### 3. Mini Scout internal layer

Script:

`/root/aitestarena/tools/run_mini_scout_internal_pipeline.sh`

Cron:

`14,34,54 * * * *`

Purpose:

Read the active watchlist, select top 1–3 internal shortlist cards, and prepare compact GPT input JSON.

This layer must not overwrite public watchlist/vitrina.

It does not call GPT and does not write agent decisions.

## Invariant

Public vitrina is not a shortlist and not a winners page.

Mini Scout shortlist is internal only and lives under:

- `/root/aitestarena/state/mini_scout_prefilter_latest.json`
- `/root/aitestarena/state/mini_scout_cycle_latest.json`
- `/root/aitestarena/state/mini_scout_gpt_input_latest.json`

Mini Scout must not write:

- `/var/www/aitestarena/watchlist/index.html`
- `/var/www/aitestarena/data/watchlist.json`

## Verified state

Public pipeline:

- status: DONE
- writes_public_vitrina: true
- calls_gpt: false
- writes_agent_decisions: false
- process_rc: 0
- render_rc: 0

Mini internal pipeline:

- status: DONE
- writes_public_vitrina: false
- public_watchlist_changed: false
- calls_gpt: false
- writes_agent_decisions: false
- selected_count: 2
- gpt_input_mode: dry_run_input_only_no_model_call

## Next step

Observe one scheduled cron cycle:

wake -> public -> mini

Only after stable cron behavior, add a separate dry-run GPT layer that reads:

`/root/aitestarena/state/mini_scout_gpt_input_latest.json`

and writes private suggestion logs only.
