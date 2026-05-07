#!/usr/bin/env python3
"""
A/B test template for skill validation.

Copy this file into the new skill's scripts/ directory,
replace the TODO placeholders, and run from the workspace root:

    python workspace/skills/<skill_name>/scripts/ab_test_<skill_name>.py

Results are written to ab_test_result.json in the current directory.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add nanobot root to path — assumes this script lives in <skill>/scripts/
# and nanobot root is 4 levels up: <skill>/scripts/ -> <skill> -> skills -> nanobot
sys.path.insert(0, str(Path(__file__).resolve().parents[2].parent.parent))

from nanobot.agent.loop import AgentLoop


async def run_task(task: str, workspace: Path, disabled_skills: list[str]):
    """Run a single task with the given disabled_skills list."""
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
        "tools_used": list(result.tools_used) if result.tools_used else [],
    }


async def main():
    task = ""  # TODO: fill in with task description string
    skill = ""  # TODO: fill in with skill name
    workspace = Path(".")

    without_skill = await run_task(task, workspace, [skill])
    with_skill = await run_task(task, workspace, [])

    better = with_skill["success"] and not without_skill["success"]
    result = {
        "task": task,
        "skill": skill,
        "without": without_skill,
        "with": with_skill,
        "diff": {
            "better": better,
            "reason": "Skill improved task success" if better else "No measurable improvement",
        },
    }

    output_path = Path("ab_test_result.json")
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
