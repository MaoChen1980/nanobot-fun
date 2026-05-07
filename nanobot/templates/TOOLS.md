# Tool Usage Notes

Non-obvious constraints and usage patterns. Trigger rules belong in SOUL.md, not here.

## exec

- Timeout 60s default, output truncated at 10K chars. Dangerous commands blocked.
- Output header: `[cwd: ..., shell: cmd|sh]` → verify working directory and shell.
- **Chinese in URLs on Windows**: CMD uses GBK → URL-encode or use `powershell -Command`. For weather prefer Open-Meteo with coordinates.
- **node -e fails on Windows**: CMD mangles quotes. Always `write_file` → `exec node <file>` instead.
- CMD: `&&` connect, `2>nul` suppress. PowerShell: `;` separate, `$null` redirect. No `cat`/`tail`/`sed`/`awk`.

## Type-Check (Write→Check→Run)

```python
# Fast: then_check="auto" detects .py → pyright, .ts/.js → tsc
write_file(path="tools/temp.py", content="...", then_check="auto", then_exec="python tools/temp.py")
```
Manual: `npx --prefix tools pyright <file> --outputjson` (check stdout JSON `generalDiagnostics`). `tsc --noEmit --allowJs --checkJs` for .js.

## delete_file / move_file

Safer alternatives to `exec rm` / `exec mv` — workspace-guarded, single-file only, path resolved against workspace. Use these instead of shell commands for file deletion and moves. `move_file` auto-creates parent directories.

## edit_file — Line Mode

Use `first_line` + `last_line` when you know line numbers from a prior `read_file`. Faster than text matching, no read_file needed first.
```python
edit_file(path="AGENTS.md", first_line=42, last_line=48, new_text="new")
```
Line numbers 1-indexed, inclusive. When both line mode and old_text set, line mode wins.

## session_manage

Main action: `auto_clean` (batch-exclude >5KB tool results). Also `list`, `exclude`, `compress`. Trigger rules → SOUL.md §上下文管理.

## grep / glob / recall

- **grep**: `output_mode="count"` to size before reading. `fixed_strings=true` for regex chars. Binary >2MB skipped.
- **glob**: `entry_type="dirs"` for directories. `head_limit` + `offset` for pagination.
## Self-Installed Tools (workspace/tools/)

> 💡 **Write your own tools — it's easy and powerful.** Use `write_file` → `then_check="auto"` → `then_exec` to create Python/JS scripts in `workspace/tools/` in one turn. They're instantly usable via `exec` thereafter. Self-written tools are often better than shell commands because you control the output format, error handling, and avoid OS-specific quoting issues.

> ⚠ Document each tool you install below. Future agent instances will read this table and use the tools without rediscovering them.

| Tool | Command | Notes |
|------|---------|-------|
| Python analysis | `python tools/analyze.py <cmd> [args]` | Example: imports, exports, callers, callees, tree, find |
| TS analysis | `node tools/analyze.js <cmd> [args]` | Example: imports, exports, callers, callees, tree, find |
| Fast find | `node tools/fast-find.js <symbol> [dir]` | Example: regex symbol search in .ts files |

⚠ All paths relative to CWD; absolute paths also accepted.

## Known Failures — Don't Repeat

> ⚠ This section is a template. Every time you discover a dead-end approach, document it here to prevent the agent from retrying it across sessions.

| Date | What | Why failed | Verdict |
|------|------|-----------|---------|
| (date) | `corepack enable` | EPERM — needs admin | ❌ |
| (date) | `npm install -g <pkg>` | EPERM on system dir | ❌ Use `--prefix tools` |
| (date) | `node -e "..."` on CMD | Quote mangling | ❌ Use `write_file`→`exec` |
