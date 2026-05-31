# Agent Structure and Learning Map — 2026-05-31

Status: active clarification note for AITestArena / FirstMeet.

This note fixes the agent identity map before expanding historical benchmark work.

## Correct agent map

### DeepSeek / Stalker

DeepSeek is the main OpenClaw/API agent used as Stalker and the paper decision layer.

It is not a local model. It does not learn by changing weights.

It can only change behavior when the runner includes updated rules, lesson cards, or policy summaries in its prompt/context.

### Mini

Mini is the OpenAI panel agent.

It is not the Silent script.

Mini should be used as an external reasoning/review agent or blind-replay agent, with compact context supplied through the panel/project prompt or explicit lesson digest.

It should not be assumed to have server, workspace, or root access.

### Silent

Silent is the FirstMeet internal AI/operator/script logic layer.

Silent is not Mini.

If Silent behavior is script/config driven, it learns through explicit rules, config, deterministic filters, and logic changes, not by model fine-tuning.

### Writer

Writer is only for psychology-channel content and FirstMeet AI comments.

Writer is not an AITestArena betting/watchlist role and should not be used for AITestArena operational decisions.

### Sentinel

Sentinel is read-only OK/WARN/FAIL monitoring.

Sentinel reports status and must not repair, write decisions, edit runtime, or change operational state.

### Evaluator

Evaluator is not a forecasting agent.

Evaluator is deterministic. It joins historical decisions with post-event outcomes and calculates metrics.

Evaluator output must not become agent input.

## Learning model

The project does not train model weights.

Learning means:

1. Historical data is analyzed deterministically.
2. The analysis creates compact lesson cards.
3. Lesson cards become role-specific policy/context updates.
4. The correct runtime or panel workflow receives those updates.
5. Blind replay checks whether behavior improved.
6. Evaluator measures the result.

A file in the repository is not memory by itself. It affects an agent only if the relevant runner, prompt, panel, or script actually reads it.

## Agent-specific learning paths

DeepSeek / Stalker:

- learns operationally through OpenClaw prompt/context injection;
- needs a Stalker policy card that the runner actually loads.

Mini:

- learns operationally through OpenAI panel/project context or explicit prompt;
- should receive compact lesson summaries, not large datasets.

Silent:

- learns operationally through script rules, configs, and deterministic logic;
- if executable behavior is needed, prefer structured config over long prose.

Evaluator:

- does not learn;
- only measures.

## No-root rule for agents

Agents without root access must receive workspace-relative tasks only.

Do not give them tasks requiring root paths, server-wide search, mail tools, cron changes, production files, or live operational files.

Root/terminal access is used only for controlled verification and external audit summaries.

## Historical benchmark rule

Historical benchmark actions are separate from live paper decisions.

Historical actions use terms like:

- PICK
- PASS
- NO_DATA
- VOID
- BASELINE_PICK

Live AITestArena keeps ENTER / WAIT / SKIP only in the live paper-decision layer.

Historical benchmark files must not be mixed into live decision files, current watchlist, paper positions, bankroll, settlement, public watchlist, or the current paper-agent cycle.

## Next safe step

Create role-specific learning artifacts:

- `docs/historical_benchmark/lessons/LESSONS_LATEST.md`
- `docs/historical_benchmark/agent_policy/DEEPSEEK_STALKER_POLICY_CARD.md`
- `docs/historical_benchmark/agent_policy/MINI_OPENAI_PANEL_POLICY_CARD.md`
- `docs/historical_benchmark/agent_policy/SILENT_LOGIC_POLICY_CARD.md`

Then define which runtime or human workflow actually loads each file.
