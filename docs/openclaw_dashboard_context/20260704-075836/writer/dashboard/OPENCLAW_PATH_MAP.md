# OpenClaw Path Map

## Canonical Writer workspace

HOST:
    /root/openclaw/workspace/writer

CONTAINER:
    /home/node/.openclaw/workspace/writer

Это один и тот же workspace через bind mount.

## Mounts

HOST /root/openclaw/workspace
-> CONTAINER /home/node/.openclaw/workspace

HOST /root/openclaw/data
-> CONTAINER /home/node/.openclaw

## Publication board

Реальный файл:
    /root/openclaw/workspace/writer/state/publication_board.md

Совместимый путь:
    /root/openclaw/workspace/writer/publication_board.md
    -> state/publication_board.md

В контейнере:
    /home/node/.openclaw/workspace/writer/publication_board.md

## Sessions

HOST:
    /root/openclaw/data/agents/*/sessions

CONTAINER:
    /home/node/.openclaw/agents/*/sessions

## Telegram spools

HOST:
    /root/openclaw/data/telegram/ingress-spool-*

CONTAINER:
    /home/node/.openclaw/telegram/ingress-spool-*

## Rule

На сервере работать через /root/openclaw/...
Внутри контейнера OpenClaw видит это как /home/node/.openclaw/...
