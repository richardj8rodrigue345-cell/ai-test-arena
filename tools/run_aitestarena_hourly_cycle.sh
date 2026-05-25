#!/usr/bin/env bash
set -u

cd /root/openclaw/workspace/aitestarena || exit 1

LOG="logs/aitestarena_hourly_cycle.log"
mkdir -p logs

ts() { date -u +%FT%TZ; }

# Source of truth note:
# This wrapper runs the paper-agent cycle only.
# The final public identity/bankroll guard is intentionally outside this wrapper
# in root crontab, after the wrapper fully exits:
# ops/cron/root_aitestarena_hourly_cycle_outer_guard.cron
# Do not re-add EXIT traps or internal identity guards here; they were tested and
# were not sufficient because later public-safe/finalize steps could still
# overwrite /agents/ before process completion.

{
  echo "$(ts) CYCLE_START"

  echo "$(ts) step=deepseek_safe_runner"
  ./tools/run_deepseek_watchlist_safe.sh --apply
  deepseek_rc=$?
  echo "$(ts) deepseek_safe_runner_rc=$deepseek_rc"

  echo "$(ts) step=settlement"
  python3 /root/aitestarena/tools/settle_agent_positions_from_watchlist.py --apply
  settlement_rc=$?
  echo "$(ts) settlement_rc=$settlement_rc"

  echo "$(ts) step=recount_enter_voids_as_counted"
  python3 /root/aitestarena/tools/recount_enter_voids_as_counted.py --apply
  recount_rc=$?
  echo "$(ts) recount_enter_voids_as_counted_rc=$recount_rc"

  echo "$(ts) step=agent_results_analysis"
  python3 /root/aitestarena/tools/analyze_agent_paper_results.py
  results_analysis_rc=$?
  echo "$(ts) results_analysis_rc=$results_analysis_rc"

  echo "$(ts) step=render"
  python3 /root/aitestarena/tools/render_agents_leaderboard.py
  render_agents_rc=$?

  python3 /root/aitestarena/tools/render_silent_gpt55_training.py
  render_silent_rc=$?

  python3 /root/aitestarena/tools/process_watchlist_outbox.py
  process_watchlist_rc=$?

  python3 /root/aitestarena/tools/render_agents_public_safe.py
  render_agents_public_clean_rc=$?

  echo "$(ts) render_agents_rc=$render_agents_rc render_silent_rc=$render_silent_rc process_watchlist_rc=$process_watchlist_rc render_agents_public_clean_rc=$render_agents_public_clean_rc"

  if [ "$deepseek_rc" -eq 0 ] \
    && [ "$settlement_rc" -eq 0 ] \
    && [ "$recount_rc" -eq 0 ] \
    && [ "$results_analysis_rc" -eq 0 ] \
    && [ "$render_agents_rc" -eq 0 ] \
    && [ "$render_silent_rc" -eq 0 ] \
    && [ "$process_watchlist_rc" -eq 0 ] \
    && [ "$render_agents_public_clean_rc" -eq 0 ]; then
    echo "$(ts) CYCLE_DONE status=OK"
    exit 0
  fi

  echo "$(ts) CYCLE_DONE status=WARN"
  exit 1
} >> "$LOG" 2>&1
