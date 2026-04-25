---
name: skill-builder
description: Detects patterns worth codifying as skills, creates them via skill-creator, validates loading/triggering, and A/B-tests their effect on behavior.
---

# skill-builder

## When to Consider Creating a Skill

- Same task done repeatedly (3+ similar requests)
- Complex workflow with many steps that could be one command
- Tool combinations used frequently together
- Knowledge domain without skill coverage

## Phase 1: Detection

Monitor conversation for patterns. When found, propose:

「这个 [task type] 已经出现 N 次，建议做成 skill: [name] — [one-line description]」

## Phase 2: Creation

1. Scaffold the skill:
   exec(python nanobot/skills/skill-creator/scripts/init_skill.py <name> --path workspace/skills --resources scripts,references)

2. LLM fills in SKILL.md with actual content

3. Validate structure:
   exec(python nanobot/skills/skill-creator/scripts/quick_validate.py workspace/skills/<name>)

4. Fix errors until validation passes

## Phase 3: Load & Trigger Validation

Before A/B testing, verify the skill loads correctly:

1. Check registration (skill appears in skills index):
   exec(python -c "from nanobot.agent.skills import SkillsLoader; from pathlib import Path; print(SkillsLoader(Path('workspace')).build_skills_summary())")

2. Check loadability (SKILL.md parses and has content):
   read_file(workspace/skills/<name>/SKILL.md)

3. Check trigger (for always=true, content appears in system prompt):
   The skill content should appear in the system prompt when the skill is active.

If any check fails → fix the skill before proceeding to A/B.

## Phase 4: A/B Behavior Test

1. Write the A/B test script to workspace (template below)

2. Fill in `provider` from current AgentLoop instance (see references/ab_test_reference.md)

3. Run the test:
   exec(python workspace/ab_test_<skill>.py)

4. Read results:
   read_file(workspace/ab_test_result.json)

5. Analyze: Did the skill cause better behavior?

## Decision Table

| A/B Result | Action |
|---|---|
| Skill → success; No skill → fail | Keep |
| Both succeed, skill fewer tokens | Keep (more efficient) |
| No measurable difference | Revise or discard |
| Skill causes worse outcome | Discard and investigate |

## A/B Test Script Template

nanobot writes this to `workspace/ab_test_<skill>.py` before running:

```python
#!/usr/bin/env python3
"""A/B test for skill: <skill_name>"""
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nanobot.agent.loop import AgentLoop

async def run_task(task, workspace, disabled_skills):
    loop = AgentLoop(
        workspace=workspace,
        provider=None,  # TODO: fill in from current AgentLoop.provider
        disabled_skills=disabled_skills,
    )
    result = await loop.process_direct(task)
    return {
        "success": result.stop_reason == "completed",
        "tool_events": result.tool_events,
        "stop_reason": result.stop_reason,
        "tools_used": list(result.tools_used) or [],
    }

async def main():
    task = "<task_description>"
    skill = "<skill_name>"
    workspace = Path(".")
    w = await run_task(task, workspace, [skill])
    with_skill = await run_task(task, workspace, [])
    result = {
        "task": task, "skill": skill,
        "without": w, "with": with_skill,
        "diff": {
            "better": with_skill["success"] and not w["success"],
            "reason": "Skill improved" if with_skill["success"] and not w["success"] else "No improvement",
        },
    }
    Path("ab_test_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
```

## Resources

- scripts/ab_test_template.py — copy-paste template for writing the A/B test script
- references/ab_test_reference.md — how to get provider, how to interpret results
