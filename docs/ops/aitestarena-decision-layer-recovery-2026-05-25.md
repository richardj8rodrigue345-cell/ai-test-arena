# AITestArena decision-layer recovery — 2026-05-25

Paper-only recovery note. No real-money betting. No manual bankroll/history edits.

## Confirmed

- DeepSeek/Stalker decision path was restored to the point where DeepSeek API calls work and paper decisions are generated.
- Latest observed DeepSeek decision mix: ENTER=0, WAIT=7, SKIP/NO_VALUE=1.
- No ENTER was expected under current guards because candidates were mostly one-source / need second source / low EV / Kelly caution.
- `direct_deepseek_runner.py` includes prompt-aware actionable fingerprint marker:
  `AITESTARENA_PROMPT_AWARE_FINGERPRINT_20260525_V2`.
- `normalize_agent_decisions.py` writes importer-compatible CSV header:
  `AITESTARENA_NORMALIZER_WRITES_HEADER_20260525`.
- `record_agent_decision.py` includes event lookup fallback:
  `AITESTARENA_RECORD_LOOKUP_FALLBACK_20260525`.
- DeepSeek ledger append was confirmed by new 2026-05-25 entries.
- Public `/agents/` smoke was OK: 3 agents, bankroll 1000, histories visible.
- Public `/watchlist/` smoke was OK after restore: no internal / settlement / PnL markers.

## Caution

During internal decision-layer work, public `/watchlist/` was briefly overwritten by an internal calculation contour and then restored. Future internal work must include public `/watchlist/` smoke checks and should consider a dedicated public vitrina guard.

## Terminal summary protocol

Use `/root/openclaw/ops/mail_terminal_summary.py`; do not rely on system mail/sendmail. Confirmed working topic:
`AITestArena cycle vitrina importer status 20260525-075557`.

## Safety invariants

All operations are virtual-credit / paper-only. Settlement is the official write step. Analysis is read-only. Writer and Sentinel must not touch decisions, bankroll, settlement, or watchlist state.
