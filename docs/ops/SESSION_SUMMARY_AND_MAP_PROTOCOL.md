# AITestArena — Session Summary and Map Protocol

Updated: 2026-05-27

This protocol records a process lesson from the 2026-05-27 AITestArena stabilization session.

## Core idea

Terminal summary emails are not just notifications. In this project they are the factual operation log.

Because ChatGPT can search Gmail terminal summaries, these emails can be used to reconstruct the real session map: what commands were run, which paths were touched, which files changed, which smoke checks passed, which backups exist, and what must not be treated as active truth.

This is especially useful when GitHub or NotebookLM is stale, incomplete, or missing runtime-only files.

## Why this matters

During the 2026-05-27 session, Gmail terminal summaries found the Sentinel launch chain faster than GitHub navigation, because the full GitHub safe snapshot initially missed the Sentinel launch files.

Gmail evidence showed:

- cron: `/etc/cron.d/aitestarena_sentinel_monitor`
- runner: `/root/aitestarena/tools/run_aitestarena_wake_sentinel.sh`
- log: `/root/aitestarena/logs/aitestarena_sentinel_monitor.cron.log`
- state: `/root/aitestarena/state/sentinel/sentinel_monitor_latest.json`
- model report: `/root/aitestarena/state/sentinel/sentinel_model_latest.json`
- task: `/root/openclaw/workspace/sentinel/tasks/SENTINEL_CURRENT_TASK.md`

After this was discovered through Gmail, the missing Sentinel files were added to the GitHub safe snapshot.

## Required end-of-session workflow

After every important AITestArena session, do this in order:

1. Send compact terminal summaries for important commands using:
   `/root/openclaw/ops/mail_terminal_summary.py`
2. Search Gmail for the session summaries:
   `subject:"FirstMeet: terminal summary" AITestArena newer_than:1d`
3. Build a dated session map from the terminal summaries.
4. Put the map in GitHub under:
   `docs/ops/SESSION_TERMINAL_SUMMARY_MAP_YYYY-MM-DD.md`
5. The session map must include:
   - operation topics;
   - key paths;
   - changed files;
   - backup paths;
   - cron entries;
   - public smoke URLs;
   - state files;
   - read-only/write boundaries;
   - what was intentionally not changed;
   - unresolved gaps.
6. Use the session map to check whether the GitHub safe snapshot is complete.
7. If GitHub cannot answer practical questions from the session, add the missing safe files.
8. Only then update NotebookLM / Google Doc pointers.

## Control questions for snapshot completeness

After pushing a safe snapshot, GitHub should be able to answer these questions without Gmail:

- How does Sentinel start?
- How does DeepSeek/Stalker start?
- Where is the 07-cycle wrapper?
- Where is settlement performed?
- Where is analysis read-only?
- Where is bankroll calculated?
- Where is public `/agents/` rendered?
- Where is public `/watchlist/` rendered?
- Where are public smoke URLs documented?
- Which old sources are stale?

If GitHub cannot answer one of these, the snapshot is incomplete.

## Terminal summary content standard

Each useful terminal summary should contain:

- short topic;
- working directory;
- command or report path;
- status and exit code;
- key stdout only, not long logs;
- touched paths;
- changed files;
- backup directory if any;
- smoke test result;
- explicit `NO CHANGE` line for protected areas such as runtime, cron, bankroll, positions, public files, or secrets when they were not touched.

Do not send secrets, tokens, passwords, private client data, `.env`, raw private submissions, or long logs.

## Preferred source stack after this protocol

1. Gmail terminal summaries = evidence log of what really happened.
2. GitHub `docs/ops` = compressed navigation and protocol layer.
3. GitHub `runtime/` and `public-current/` = safe snapshot of active files.
4. NotebookLM Active Source / 00 START = high-level context entry.
5. VPS/server = runtime truth, checked narrowly after navigation.

## Practical rule

Do not build GitHub navigation from assumptions alone. Build it from terminal summary evidence first, then verify with narrow server checks.

The correct direction is:

`server operation -> terminal summary email -> Gmail session map -> GitHub navigation/snapshot -> NotebookLM index`

not:

`memory -> broad grep -> guessed file map`.
