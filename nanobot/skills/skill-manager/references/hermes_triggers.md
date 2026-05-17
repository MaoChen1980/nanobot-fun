# Hermes Trigger Conditions (Source Reference)

This document captures the original trigger conditions from Hermes Agent's `skill_manage` tool description and `skill_commands.py`, used as reference for nanobot's skill-builder.

## When to CREATE a Skill

Hermes uses these conditions — follow the same spirit:

- **Complex task succeeded (5+ tool calls)** — A multi-step task that required significant reasoning
- **Errors overcome with workarounds** — You found a solution to a non-obvious error
- **User corrected your approach** — User explicitly corrected your method, and it worked
- **Non-trivial workflow discovered** — A workflow that required significant reasoning to find
- **User asks to remember a procedure** — Explicit request from user
- **Frequent tool combination** — Tools used together repeatedly

## When to PATCH a Skill

- **You used a skill and hit issues not covered by it** → patch immediately
- **Skill failed in a specific environment** (e.g., Windows path issues)
- **You found a better approach after creating it**

## When to DELETE a Skill

- **Replaced by a better alternative**
- **Superseded by a framework feature**
- **Initial design was completely wrong**
- **Continuously causes worse outcomes**

## Hermes Security Notes

Hermes skills are scanned by `skills_guard.scan_skill()` before being saved. nanobot does not currently have this — consider adding if installing skills from external sources.