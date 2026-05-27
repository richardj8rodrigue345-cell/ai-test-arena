# AITestArena internal contour recovery — 2026-05-27

Status: active source-control note.

Scope: recovery and stabilization of the AITestArena / OpenClaw paper-only operational contour. No real-money betting, no gambling account actions, and no manual bankroll/history/positions edits were performed.

## Final active state

- Writer remains limited to psychology-channel content and FirstMeet AI comments; Writer is not AITestArena.
- Stalker / Decision layer is paper-only and uses `ENTER / WAIT / SKIP` in `agent_decisions.csv`.
- `SENT_NO_BET` is an operational no-bet report in `no_bet_reports.jsonl`, not a betting decision.
- Sentinel remains read-only `OK / WARN / FAIL` and must not write decisions, bankroll, public pages, cron, or code.
- 07-cycle wrapper remains `runner -> settlement(write) -> recount -> analysis(read) -> render -> CYCLE_DONE`.
- Final identity guard remains outer cron, not an internal `EXIT` trap.

## Key fixes and active runtime facts

1. Public `/agents/` was restored and public-safe finalized after earlier blank/stale-page symptoms. Public `/agents/`, `/watchlist/`, and `/data/watchlist.json` returned HTTP 200 in smoke checks.
2. Public watchlist source metadata was sanitized. Public watchlist JSON should use `source=public_watchlist` rather than internal paths such as `candidate_events.csv` or `/root/openclaw/...`.
3. DeepSeek wake hook no longer ends at `NO_DEEPSEEK_DELIVERY_BACKEND`. The active hook now calls `/root/openclaw/workspace/aitestarena/run_deepseek_watchlist_safe.sh`.
4. DeepSeek hourly apply is enabled after guards were installed: `/root/aitestarena/tools/run_deepseek_watchlist_once.sh` now calls `timeout 420 "$SAFE" --apply`.
5. The safe runner has transactional protection marker `AITESTARENA_DECISION_GUARD_20260527`, so `agent_decisions.csv` is backed up and restored if `direct_deepseek_runner.py` fails or output becomes header-only.
6. The safe runner has normalize skip marker `AITESTARENA_NORMALIZE_SKIP_ONLY_20260527`. If no new decision rows are added, normalize is skipped and `agent_decisions.csv` is not rewritten destructively.
7. The wrong whole-file validation call `record_agent_decision.py --dry-run "$DEC"` was replaced by CSV schema validation. `record_agent_decision.py` is a CLI for one decision and must not be used as a whole-file validator.
8. Active decision schema is `ENTER / WAIT / SKIP`. `YES/NO` is not the current active AITestArena decision schema. `ENTER` may create a paper position; `WAIT/SKIP` do not create an open paper position. `SENT_NO_BET` only means the agent made a pass with no new decision.
9. Canonical outbox is `/root/openclaw/workspace/aitestarena/aitestarena_watchlist_outbox`. The older `/root/openclaw/workspace/aitestarena_watchlist_outbox` is legacy/reference and should not be treated as the active write path.
10. Manual guarded `--apply` test succeeded after fixes: `apply_rc=0`, `decisions_before=13`, `decisions_after=13`, `decisions_not_truncated=OK`. No new decision was added during that test; `SENT_NO_BET` was written when no new decision appeared.
11. DeepSeek hourly apply final check succeeded: `hourly_apply_enabled=true`, `hook_syntax=OK`, `hook_rc=0`, `decisions_not_truncated=OK`, `no_bet_reports.jsonl` grew to 3 lines, and `PUBLIC_SAFE_CHECK_OK` / `finalize_rc=0` were observed.
12. Sentinel/controller verification after apply showed Sentinel monitor and model report status `OK`, `read_only=true`, `writes_bankroll=false`, `writes_positions=false`, `writes_agent_decisions=false`, `writes_public_pages=false`. Latest observed `CYCLE_DONE` entries included `2026-05-27T11:07:06Z status=OK`.

## Important files / paths

- `/root/aitestarena/tools/run_deepseek_watchlist_once.sh` — hourly DeepSeek wake hook, now safe-runner apply bridge.
- `/root/openclaw/workspace/aitestarena/run_deepseek_watchlist_safe.sh` — guarded safe runner.
- `/root/openclaw/workspace/aitestarena/direct_deepseek_runner.py` — DeepSeek model runner.
- `/root/openclaw/workspace/aitestarena/aitestarena_watchlist_outbox/agent_decisions.csv` — canonical paper decisions outbox.
- `/root/openclaw/workspace/aitestarena/aitestarena_watchlist_outbox/no_bet_reports.jsonl` — `SENT_NO_BET` report log.
- `/root/aitestarena/tools/finalize_public_safe_pages.py` — public-safe finalization.
- `/root/aitestarena/state/sentinel/sentinel_monitor_latest.json` and `sentinel_model_latest.json` — Sentinel read-only monitor/model state.

## Operational interpretation

- If new valid paper value appears, DeepSeek may write `ENTER / WAIT / SKIP` during hourly apply.
- If no new valid decision appears, DeepSeek should write `SENT_NO_BET` rather than silently doing nothing.
- Missing `ENTER` is not by itself a failure.
- Any future attempt to modify apply/normalization/import must preserve the decision guard and must never leave `agent_decisions.csv` header-only.
- Real-money betting remains forbidden.

## Post-save check

After the next cron cycle, verify:

- `agent_decisions.csv` line count;
- latest `no_bet_reports.jsonl` row;
- `/agents/` HTTP 200;
- `/watchlist/` HTTP 200;
- `PUBLIC_SAFE_CHECK_OK`;
- Sentinel status `OK`.

Then ask NotebookLM `ACTIVE CONTEXT CHECK`. Expected verdict: `CONTEXT OK`.
