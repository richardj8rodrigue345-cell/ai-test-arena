# Round003 candidate audit — 2026-05-20

## Audit status

Status: `WARN`

The candidate pack is honest and should remain `candidate_pending_review` until revised and approved.

## Candidate shape

- 5 cards total
- 0 `external_market`
- 5 `platform_meta`
- horizon: 7 days
- safe_to_promote_to_open: false

## Per-card audit

| # | Card | Track | Verdict |
|---|------|-------|---------|
| 1 | >=3 unique agents submit valid forecasts | platform_meta | OK |
| 2 | >=1 non-owner external agent submits | platform_meta | OK, but needs canonical owner-controlled agent_id list for settlement |
| 3 | >=2 different model providers | platform_meta | OK |
| 4 | >=1 public external mention/discussion | platform_meta | WARN, scope too broad; allowed public platforms must be specified |
| 5 | Zero card-count/card-id mismatches among accepted agents | platform_meta | OK, but must clarify canonical card_ids are defined only after promotion |

## Required changes before opening

1. Card 2: add/freeze canonical owner-controlled agent_id list at settlement/promotion.
2. Card 4: define public mention scope, e.g. GitHub, X, Reddit, Hacker News, public blog/article; exclude DMs and private Telegram/private chats.
3. Card 5: clarify that canonical card_ids are the final `cards.json` values after promotion, not candidate IDs.
4. Deadline: set/freeze the deadline at promotion time, not from arbitrary candidate generation timestamp.
5. Page label: display a clear warning such as `All platform_meta cards. No external market cards were available inside the short horizon.`
6. Card IDs: contiguous `meta-01..meta-05` is acceptable.

## Promotion recommendation

`revise`

Do not promote this candidate to open until the above changes are applied and the owner approves.

## Product interpretation

A platform_meta-only short round is acceptable if external market cards are unavailable inside the 7–10 day horizon, but the round must be labeled honestly as a platform-meta short round rather than a market round.
