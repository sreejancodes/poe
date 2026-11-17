# Phase 01: update the skill and README

Depends on: nothing. Plan: `plans/poe-dir-and-logs/plan.md` (read it first; it is the source of truth).

One unit. `SKILL.md` and `README.md` must describe the same layout, so they are edited together by one worker rather than split across two.

## Unit 01a: rename output root, add summary and log-copy step

**Goal.** Implement sections 1–4 of the plan's Approach: move all poe output from `plans/<slug>/` to `poe/<slug>/`, add `summary.md` written at the end of `execute`/`resume`, add a short "Logs" section with the copy step, and update the README to match.

**Inputs to read.**

- `plans/poe-dir-and-logs/plan.md`
- `skills/poe/SKILL.md` (100 lines)
- `README.md` (104 lines)
- `agents/phase-worker.md` (16 lines; check only, expected unchanged)
- Claude Code skills docs, https://code.claude.com/docs/en/skills, to confirm the `${CLAUDE_SESSION_ID}` substitution (plan's Assumptions, second bullet). Also check whether a different name or an environment variable is documented for the session ID.

**Files it may change.**

- `skills/poe/SKILL.md`
- `README.md`
- `agents/phase-worker.md` only if it turns out to mention the output path

**Steps.**

1. Confirm `${CLAUDE_SESSION_ID}` in the docs. Record the finding (with the doc URL and quoted wording) in the progress notes. If it is not supported, use the plan's fallback (newest `.jsonl` in the project's transcript folder) and say so in the notes; do not invent another mechanism.
2. `SKILL.md`:
   - Replace every `plans/` reference with `poe/` (Files section, default-path rule under Operating modes, plan-mode step 2).
   - Add `summary.md` and `logs/<session-id>/...` to the Files layout block, matching the plan's section 1.
   - Execute mode, final step: write `summary.md` (overwritten each run) with what passed, what remains uncertain, blockers, and file locations. Same for `resume` when it finishes or stops.
   - Add a short "Logs" section: when to copy (end of every mode, and when stopping for user input mid-execution), the copy command, that re-running overwrites, that the copy is a snapshot, and that a missing source is reported and never blocks the task.
   - In the command, search `"${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects"` (use `$HOME`, not `~`, inside the expansion), and quote all paths.
3. `README.md`:
   - Usage examples and Files section: `plans/` → `poe/`.
   - Add `summary.md` and `logs/` to the layout block.
   - Short note: logs contain the full conversation (file contents, command output); normally add `poe/*/logs/` (or `poe/`) to `.gitignore`. Replace the existing "Decide per repository whether to track `plans/`" line accordingly.
   - One migration line: `mv plans/<slug> poe/<slug>`.
4. Keep edits minimal and in the existing style. No new sections beyond "Logs" in SKILL.md and the notes above in README.

**Non-goals.** No scripts, hooks, config options, parsers, or dashboards. Do not touch `.claude-plugin/*.json` or `LICENSE`. Do not move this task's own files out of `plans/poe-dir-and-logs/` (the installed poe version still uses `plans/`). Do not commit.

**Verification commands.**

```sh
grep -rn "plans/" skills agents README.md
# expected: only the README migration line (mv plans/<slug> poe/<slug>) and, if present,
# a note that an explicit old plans/... path still works. Nothing else.
grep -n "poe/" skills/poe/SKILL.md README.md
grep -n -e "summary.md" -e "logs/" skills/poe/SKILL.md README.md
# both files must mention summary.md and logs/
claude plugin validate . 2>&1 || echo "validate not available"
```

Also test the copy command itself in a shell against the current session (the worker's own session or any existing `.jsonl` under `~/.claude/projects`), writing into a scratch directory, not into the repo. Confirm the copied file parses: `python3 -c 'import json,sys; [json.loads(l) for l in open(sys.argv[1])]' <copied file>`.

**Completion criteria.**

- All verification commands run and their output recorded in the notes.
- `SKILL.md` and `README.md` describe the same layout (including `summary.md` and `logs/`).
- The `${CLAUDE_SESSION_ID}` finding is recorded with its source.
- The copy command was run at least once outside the repo and the result parsed.

**Progress notes:** `plans/poe-dir-and-logs/progress/01a-docs.md`
