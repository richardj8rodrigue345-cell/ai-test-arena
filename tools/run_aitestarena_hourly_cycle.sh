#!/usr/bin/env bash
# AITESTARENA_FINAL_IDENTITY_GUARD_EXIT_TRAP_20260525
aitestarena_final_identity_guard() {
  local rc="$?"
  if [ -f /root/aitestarena/tools/enforce_mini_scout_identity.py ]; then
    /usr/bin/python3 /root/aitestarena/tools/enforce_mini_scout_identity.py >> /root/aitestarena/logs/mini_scout_identity_guard.log 2>&1 || true
  fi
  exit "$rc"
}
trap aitestarena_final_identity_guard EXIT

set -u

cd /root/openclaw/workspace/aitestarena || exit 1

LOG="logs/aitestarena_hourly_cycle.log"
mkdir -p logs

# Always finalize safe public pages as the final visible state.
cleanup_public_safe_pages() {
  echo "$(date -u +%FT%TZ) final_step=finalize_public_safe_pages"
  python3 /root/aitestarena/tools/finalize_public_safe_pages.py
  echo "$(date -u +%FT%TZ) final_step=finalize_public_safe_pages_done rc=$?"
}
trap cleanup_public_safe_pages EXIT


ts() { date -u +%FT%TZ; }

{
  echo "$(ts) CYCLE_START"

  echo "$(ts) step=deepseek_safe_runner"
  ./tools/run_deepseek_watchlist_safe.sh --apply
  deepseek_rc=$?
  echo "$(ts) deepseek_safe_runner_rc=$deepseek_rc"

  echo "$(ts) step=settlement"
  python3 /root/aitestarena/tools/settle_agent_positions_from_watchlist.py --apply
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) step=recount_enter_voids_as_counted"
python3 /root/aitestarena/tools/recount_enter_voids_as_counted.py --apply || echo "recount_enter_voids_as_counted_rc=$?"
  settlement_rc=$?
  echo "$(ts) settlement_rc=$settlement_rc"
  # AITESTARENA_AGENT_RESULTS_ANALYSIS_AFTER_SETTLEMENT
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

  if [ "$deepseek_rc" -eq 0 ] && [ "$settlement_rc" -eq 0 ] && [ "$results_analysis_rc" -eq 0 ] && [ "$render_agents_rc" -eq 0 ] && [ "$render_silent_rc" -eq 0 ] && [ "$process_watchlist_rc" -eq 0 ] && [ "$render_agents_public_clean_rc" -eq 0 ]; then
    # AITESTARENA_IDENTITY_GUARD_INSIDE_SUCCESS_20260525
    echo "$(ts) step=identity_guard_after_hourly"
    /usr/bin/python3 /root/aitestarena/tools/enforce_mini_scout_identity.py >> /root/aitestarena/logs/mini_scout_identity_guard.log 2>&1
    identity_guard_rc=$?
    echo "$(ts) identity_guard_rc=$identity_guard_rc"
    if [ "$identity_guard_rc" -eq 0 ]; then
      echo "$(ts) CYCLE_DONE status=OK"
      exit 0
    fi
    echo "$(ts) CYCLE_DONE status=WARN identity_guard_failed"
    exit 1
  fi

  echo "$(ts) CYCLE_DONE status=WARN"
  exit 1
} >> "$LOG" 2>&1

# AITESTARENA_IDENTITY_GUARD_AFTER_HOURLY
# Keep public Agents identity stable after the hourly paper-agent cycle renders pages.
if [ -f /root/aitestarena/tools/enforce_mini_scout_identity.py ]; then
  /usr/bin/python3 /root/aitestarena/tools/enforce_mini_scout_identity.py >> /root/aitestarena/logs/mini_scout_identity_guard.log 2>&1 || echo "identity_guard_after_hourly_failed rc=$?"
fi

