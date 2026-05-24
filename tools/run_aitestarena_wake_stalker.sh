#!/usr/bin/env bash
set -euo pipefail

if [ -x /root/aitestarena/tools/hourly_deepseek_watchlist_wakeup.sh ]; then
  timeout 90s /root/aitestarena/tools/hourly_deepseek_watchlist_wakeup.sh
else
  echo "missing hourly_deepseek_watchlist_wakeup.sh"
  exit 1
fi
