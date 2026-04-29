---
name: session-restore-sequence
description: Restore cross-session context when starting a new session. Read SESSION.md → MEMORY.md → goals.md → capability.md → process-log.md (last 30 lines) → check HEARTBEAT.md for blocked tasks. Use automatically on every new session start, without user prompting.
---

# Session Restore Sequence

## When to Use
- **Automatically** at the start of every new session
- When context has been reset and previous state needs to be recovered
- The agent should run this sequence without user prompting

## Steps (in order)

### 1. Read SESSION.md
- Contains the last session's state snapshot
- First 3 lines are injected into system prompt on restart (context.py:153-159)
- Gives immediate continuity from previous session

### 2. Read MEMORY.md
- User preferences, hard constraints, active projects
- Framework constraints that affect action boundaries
- Recent decisions for context

### 3. Read goals.md
- Current active goals and their status
- Blocked goals that may need attention

### 4. Read capability.md
- Installed tools and their capabilities
- What the agent can currently do

### 5. Read process-log.md (last 30 lines)
- Use `read_file("memory/process-log.md", offset=-30)` or read the tail
- Shows what was being worked on, what was completed, what's in progress
- Critical for resuming interrupted multi-step tasks

### 6. Check HEARTBEAT.md
- Look for any Active Tasks that are blocked or need progression
- If found, prioritize advancing these tasks
- HEARTBEAT.md tracks cross-session tasks that span multiple sessions

### 7. Synthesize and Report
- Brief summary to user: "Restored from previous session. Active: [goals]. In progress: [tasks]."
- If HEARTBEAT tasks found: "I have [N] pending tasks from previous sessions. Continue with [priority task]?"

## Quality Rules
- Never skip a step — each file may contain critical state
- If a file doesn't exist, note it and continue (don't error)
- process-log.md last-30-lines is the minimum; read more if context is light
- HEARTBEAT.md check is mandatory — this is how cross-session tasks survive resets
- This skill should trigger implicitly; the user should not need to request context restoration
