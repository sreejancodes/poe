# Phase 02: end-to-end validation

Depends on: phase 01 verified.

## Unit 02a: run plan → split → execute on a trivial task with the local plugin

**Goal.** Check the plan's runtime acceptance criteria (third and fourth bullets) by running the modified plugin end to end in a scratch directory.

**Inputs to read.**

- `plans/poe-dir-and-logs/plan.md` (Acceptance criteria, Testing and validation)
- `plans/poe-dir-and-logs/progress/01a-docs.md` (what phase 01 changed and found)
- `skills/poe/SKILL.md` (the new Logs section)

**Files it may change.** None in the repository. It works only in a fresh scratch directory outside the repo (e.g. under the session scratchpad), and writes its progress notes.

**Steps.**

1. Create an empty scratch directory with `git init` (so `resume`/`execute` git checks have something to read).
2. In that directory, run three headless sessions against the local plugin, one per mode, e.g.:
   ```sh
   claude -p --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe \
     --permission-mode acceptEdits --allowedTools "Bash(mkdir:*) Bash(cp:*) Bash(find:*)" \
     "/poe:poe plan add a hello.txt file containing 'hello'"
   ```
   then `split poe/<slug>/plan.md`, then `execute poe/<slug>/plan.md`. Adjust flags if the installed version names them differently; record the exact commands used. The permission mode used must be the one the user approved (see `status.md`).
3. Inspect `poe/<slug>/`:
   - `plan.md`, `phases/`, `status.md`, `progress/`, `summary.md` exist.
   - `logs/<session-id>/<session-id>.jsonl` exists for each of the three sessions.
   - The execute session has `logs/<session-id>/subagents/agent-*.jsonl` (and `.meta.json`).
4. For each copied main `.jsonl`, `diff` it against the original under `~/.claude/projects/...`: the copy must equal a prefix of the original (only trailing lines missing). Parse each copy with the `python3` one-liner from the plan.
5. If something fails, record exactly what and why. Do not edit `SKILL.md` or `README.md`; report back so the orchestrator can scope a fix.

**Non-goals.** No repository edits, no commits, no cleanup of `~/.claude/projects`. Do not run anything on remote systems.

**Verification commands.**

```sh
find poe -maxdepth 4 | sort
for f in poe/*/logs/*/*.jsonl; do python3 -c 'import json,sys; [json.loads(l) for l in open(sys.argv[1])]' "$f" && echo "ok $f"; done
ls poe/*/logs/*/subagents/
```

**Completion criteria.** Every check in step 3 and 4 has an observed pass/fail recorded in the notes, with the commands and their output (trimmed). Unverified items are marked as such, not assumed.

**Progress notes:** `plans/poe-dir-and-logs/progress/02a-e2e.md`
