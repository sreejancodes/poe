# Phase 03: validation on real data and end to end

Depends on: units 01b and 02a verified.

## Unit 03a: real transcripts, independent token check, `/poe:poe report` end to end

**Goal.** Check the plan's runtime acceptance criteria (Acceptance criteria bullets 2–5; Testing and validation steps 2–4).

**Inputs to read.** `poe/poe-report-dashboard/plan.md`, `progress/01a-parser.md` (usage rule), `progress/02a-render.md`, `progress/01b-docs.md`, `skills/poe/SKILL.md`.

**Files it may change.** None in the repository. Work in a scratch directory under the session scratchpad. Write only the progress notes.

**Steps.**

1. Build a scratch task `poe/real-check/` in a fresh scratch dir: copy a `plan.md` and `status.md` from any `plans/*/` dir, and copy into `logs/` the transcripts of session `7234187e-d86b-4afa-adca-ee152aac72bf` (with its `subagents/`, from `~/.claude/projects/-private-tmp-claude-1128299617--Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe-cb353a49-6d4d-41b6-911e-14acc86a0355-scratchpad-02a-e2e/`) and one or two sessions from `~/.claude/projects/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/`.
2. Run `python3 <repo>/skills/poe/scripts/poe_report.py poe/real-check`. Check, by grep/python on the HTML and by comparing with the JSONL:
   - every session and worker has a section;
   - the number of tool-call rows equals the number of `tool_use` blocks in the files, in order, each with a result;
   - every `is_error: true` result is in the Errors section;
   - token totals equal an independent `python3` sum over `message.usage` written by this unit (same dedup rule as 01a);
   - `grep -nE '(src|href)="https?:' report.html` finds nothing.
   Note the HTML size; open in a browser only if a tool for it is available, otherwise say it was not visually checked.
3. End to end: in a scratch dir holding a copy of `poe/real-check/` (without `report.html`), run headless against the local plugin, e.g.
   ```sh
   claude -p --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe \
     --permission-mode acceptEdits --allowedTools "Bash(python3:*) Bash(mkdir:*) Bash(cp:*) Bash(find:*)" \
     "/poe:poe report poe/real-check"
   ```
   using the permission mode recorded as approved in `status.md`. Confirm `report.html` is written and the reply gives its path. Record the exact command and whether any step was denied.
4. `claude plugin validate .` in the repo.
5. If something fails, record exactly what and why. Do not edit repository files; report back so the orchestrator can scope a fix.

**Non-goals.** No repository edits, no commits, no cleanup of `~/.claude/projects`, nothing on remote systems.

**Completion criteria.** Each check in steps 2–4 has an observed pass/fail with trimmed command output in the notes. Unverified items marked as such.

**Progress notes:** `poe/poe-report-dashboard/progress/03a-validation.md`
