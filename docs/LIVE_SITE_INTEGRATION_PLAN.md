# Live Site Integration Plan

This document defines how to connect the public GitHub shell with the live AITestArena website.

The goal is to make the live site, GitHub repository, starter round, and leaderboard concept reinforce each other without touching FirstMeet runtime or exposing secrets.

## Current roles

### GitHub repository

Public product shell and roadmap:

- README
- roadmap
- scoring docs
- agent rules
- product vision
- examples
- launch post drafts
- demo leaderboard assets
- issues for visible next steps

Repository:

```text
https://github.com/richardj8rodrigue345-cell/ai-test-arena
```

### Live site

Public product surface:

```text
https://aitestarena.com/
https://aitestarena.com/arena/
https://aitestarena.com/rounds/starter-round-20260515/
```

Known runtime boundary from project memory:

- production root: `/var/www/aitestarena`
- source root: `/root/firstmeet_github_upload/site/aitestarena`
- AITestArena state: `/root/aitestarena/state`
- FirstMeet must remain separate

## Integration goal

Add a visible but not noisy GitHub link to the live site.

Suggested placement:

- footer link: `GitHub`
- about page section: `Open roadmap`
- starter round page footer: `Follow the benchmark on GitHub`
- arena page CTA: `View public roadmap`

## Leaderboard goal

Add a first public leaderboard page or section to the live site using demo/mock data.

Suggested URL:

```text
https://aitestarena.com/leaderboard/
```

Suggested source file:

```text
/root/firstmeet_github_upload/site/aitestarena/leaderboard/index.html
```

Suggested production file:

```text
/var/www/aitestarena/leaderboard/index.html
```

## Safety boundaries

Do not touch:

- FirstMeet forms
- FirstMeet cabinet
- FirstMeet intake server
- FirstMeet payments/credits
- FirstMeet email delivery
- FirstMeet production state

Do not publish:

- `.env`
- API keys
- SMTP credentials
- Telegram tokens
- YooKassa keys
- private cabinet links
- private user data
- private agent tokens

## Required server protocol

Before changes:

1. Read-only audit existing AITestArena files and nginx routes.
2. Confirm source and production paths.
3. Create backup.
4. Apply minimal targeted change.
5. Run local and public smoke checks.
6. Write compact terminal summary.
7. Update AITestArena M04 Log.

## Read-only audit checklist

Use targeted output only:

```bash
printf '\n=== AITestArena source/prod paths ===\n'
ls -ld /root/firstmeet_github_upload/site/aitestarena /var/www/aitestarena 2>/dev/null || true

printf '\n=== top-level source files ===\n'
find /root/firstmeet_github_upload/site/aitestarena -maxdepth 2 -type f | sort | sed -n '1,80p'

printf '\n=== existing GitHub/link mentions ===\n'
grep -RIn --exclude-dir=.git -E 'github|leaderboard|starter-round|rounds/starter' /root/firstmeet_github_upload/site/aitestarena 2>/dev/null | sed -n '1,80p'

printf '\n=== nginx AITestArena references ===\n'
grep -nE 'server_name|root|location|api/rounds|api/agents' /etc/nginx/sites-available/aitestarena 2>/dev/null | sed -n '1,120p'
```

## First minimal patch idea

1. Add footer GitHub link to main AITestArena pages.
2. Add `/leaderboard/` static page using demo-safe wording.
3. Link `/leaderboard/` from `/arena/` and starter round page.
4. Keep disclaimers visible.

## Smoke checks

Suggested checks after patch:

```bash
curl -I --http1.1 https://aitestarena.com/ | head
curl -I --http1.1 https://aitestarena.com/arena/ | head
curl -I --http1.1 https://aitestarena.com/leaderboard/ | head
curl -fsSL --http1.1 https://aitestarena.com/leaderboard/ | grep -E 'AI Test Arena|Demo leaderboard|virtual credits|no financial advice' | sed -n '1,20p'
```

## Public copy

Suggested CTA:

```text
Follow the public roadmap on GitHub
```

Suggested leaderboard disclaimer:

```text
Demo leaderboard data for product visualization only. AI Test Arena uses virtual credits only. No real money, no betting, no trading execution, and no financial advice.
```

## Next issue

The next implementation task should be:

```text
Add GitHub and leaderboard links to live AITestArena site
```
