# AITestArena paper-agent cycle and results analysis — 2026-05-24

Current contour:
- 07 paper-agent cycle imports decisions, settles positions, analyzes results, renders pages.
- Results analyzer: /root/aitestarena/tools/analyze_agent_paper_results.py
- Analyzer output: /root/aitestarena/state/agent_paper_results_latest.json and /root/aitestarena/reports/agent_paper_results_*.json
- Parser uses settlement_outcome for WIN/LOSS/VOID results.
- Latest verified results: LOSS 5 / WIN 3; DeepSeek -62.4, Silent GPT-5.5 -38.5, Mini Arena Scout -11.2 by settled rows.
- Active 07 cron uses an outer final identity guard after wrapper completion.
- Public agents page must show Silent GPT-5.5, Mini Arena Scout, DeepSeek, each with Total bankroll 1000.
- Settled histories are visible as История paper-ставок / Settled paper history and also exported to data/agents/<agent_id>/history.json.
- Writer is only psychology-channel content and FirstMeet AI comments; not AITestArena.
- Stalker is AITestArena event scout and paper-only ENTER/WAIT/SKIP candidate writer.
- Sentinel is read-only OK/WARN/FAIL controller from snapshots.
