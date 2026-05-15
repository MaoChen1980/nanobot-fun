You are analyzing a conversation snapshot — a "saved prompt."

The saved prompt contains two parts:
1. **System prompt** — includes the agent's memory files (SOUL.md, USER.md, MEMORY.md) as they were at that moment. This is your reference for "what was already known."
2. **Conversation history** — user messages and assistant replies. This is "what happened."

## Instructions

Identify **NEW** information — facts, preferences, rules, decisions, or patterns in the conversation that are **NOT** already reflected in the system prompt's memory content.

- Do NOT extract things already present in the memory snapshot.
- If the conversation contradicts older memory, trust the LATEST statement.
- If the conversation was truncated (missing the beginning), focus on what remains — even partial context can yield valid findings.

Ignore trivial interactions like greetings, simple confirmations, or off-topic chat.

## Existing Skills (for dedup)

Do NOT suggest creating a skill that already exists. If a reusable pattern matches an existing skill, output `"type": "skip"` instead.

{existing_skills_section}

## Output Format

Respond ONLY with a JSON object matching this schema:

```json
{
  "session_summary": "<concise summary of this conversation segment>",
  "findings": [
    {
      "type": "user_preference|soul_rule|knowledge|decision|reusable_pattern|skip",
      "content": "<what was discovered>",
      "confidence": "high|medium",
      "condition": "<WHEN... for soul_rule>",
      "action": "<THEN... for soul_rule>",
      "topic": "<topic name for knowledge/decision>",
      "tags": ["<category tag for knowledge>"],
      "rationale": "<why this decision was made>",
      "name": "<kebab-case-name for reusable_pattern>",
      "steps": ["<step 1>", "<step 2>"]
    }
  ]
}
```

### Type Reference

| type | When to use | Required fields |
|------|-------------|-----------------|
| `user_preference` | A new fact about the user's preferences | content, confidence |
| `soul_rule` | A behavior rule for the agent | content, condition, action, confidence |
| `knowledge` | Technical knowledge, architecture facts | content, topic, tags, confidence |
| `decision` | An architectural or design decision | content, topic, tags, rationale, confidence |
| `reusable_pattern` | A multi-step workflow worth making a skill | content, name, steps, confidence |
| `skip` | Nothing useful found | content (brief reason) |
