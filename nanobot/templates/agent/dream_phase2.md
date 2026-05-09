Update memory files based on the analysis below.

## File scope — hard boundaries

| File | 存什么 | 不存什么 |
|------|--------|---------|
| **USER.md** | 用户身份、偏好、沟通风格、技术水平、特殊指令 | 框架机制、bug、工具说明 |
| **SOUL.md** | WHEN→THEN 行为规则、沟通风格、安全约束 | 项目细节、bug 记录 |
| **MEMORY.md** | 索引 + 近期条目摘要（链接到子文件），保持轻量 | 详细内容（放到子文件） |
| **memory/conversations/index.md** | 值得记录的对话、用户明确要记住的讨论、经验教训 | 临时的技术细节、bug 修复步骤 |
| **memory/preferences/USER_PREFERENCES.md** | 用户偏好、习惯、沟通风格、代码约定、优先级 | 框架机制、项目细节 |
| **memory/knowledge/FRAMEWORK.md** | 框架机制、约束、架构决策 | bug 记录、临时状态 |
| **memory/knowledge/DECISIONS.md** | 决策日志 — 架构和流程选择及理由 | 已完成的任务、过时的信息 |

Note: HEARTBEAT.md is NOT updated by Dream — agent maintains it during sessions. Goals and events are in DB via `write_goal`/`list_goals` and `write_event`/`list_events`.

## Output format

- [USER] entries → add to USER.md
- [SOUL] entries → add to SOUL.md
- [MEMORY-INDEX] entries → add to memory/MEMORY.md (index + recent summary)
- [MEMORY-CONVERSATION] entries → add to memory/conversations/index.md
- [MEMORY-PREFERENCE] entries → add to memory/preferences/USER_PREFERENCES.md
- [MEMORY-KNOWLEDGE] entries → add to memory/knowledge/FRAMEWORK.md or DECISIONS.md
- [MEMORY-REMOVE] entries → delete from memory/MEMORY.md
- [SKILL] entries → create skills/<name>/SKILL.md

## Editing rules
- Edit directly — file contents provided below, no read_file needed
- Use exact text as old_text, include surrounding blank lines for unique match
- Batch changes to the same file into one edit_file call
- For deletions: section header + all bullets as old_text, new_text empty
- Surgical edits only — never rewrite entire files
- If nothing to update, stop without calling tools

## Skill creation rules (for [SKILL] entries)
- Before writing, read_file `{{ skill_manager_path }}` for format reference (use `nanobot/skills/skill-manager/SKILL.md`)
- **Dedup check**: read existing skills listed below to verify no functional redundancy
- Include YAML frontmatter, keep under 2000 words, include when-to-use + steps + example + self-optimization note
- Every skill must end with: "This skill can self-optimize: fix bugs, improve steps, add edge cases, enhance verification. Do NOT change the description or trigger — they are owned by skill-manager."
- Description and trigger are the skill's invariant contract — never instruct the skill to change them
- Do NOT overwrite existing skills

## Quality
- Every line must carry standalone value
- Concise bullets under clear headers
- When reducing: keep essential facts, drop verbose details
- If uncertain whether to delete, keep but add "(verify currency)"