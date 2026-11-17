# Phase 02: end-to-end validation

Depends on: 01a verified. One unit. Analysis only: no edits to repository files.

Read first: `poe/poe-thinking-capture/plan.md` (Acceptance criteria, Testing and validation) and `poe/poe-thinking-capture/progress/01a-report.md`.

## Unit 02a: headless capture with a subagent, and static checks

**Goal.** Show, with observed output, that summarized thinking is recorded in a headless session **and in its subagent's transcript**, and that the report built from them shows it. This tests plan validation steps 3 and 5. Step 4 (the interactive check) is left to the user.

**Steps.**

1. In a fresh scratch dir `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/02a/run`, run (stdin from /dev/null):
   `claude -p --model haiku --thinking-display summarized --output-format json "<prompt>" < /dev/null > out.json`
   The prompt asks Claude to use the Agent tool to spawn exactly one general-purpose subagent that solves a small reasoning puzzle without tools and returns only the answer, then reply with that answer. If the Agent tool is refused under the default permission mode, retry once with `--allowedTools Agent` and record what happened.
2. Read `session_id` from `out.json`. Find `<session_id>.jsonl` under `~/.claude/projects` and its `<session_id>/subagents/` folder. For the main and each subagent transcript, record: the `display` value in `api-request` records, and the number of thinking blocks with and without text.
3. Build a scratch task `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/02a/poe/e2e-thinking/logs/<session_id>/` with the main `.jsonl` and the `subagents/` folder copied in. Run `python3 skills/poe/scripts/poe_report.py /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/02a/poe/e2e-thinking` and check that the report shows thinking text in both the session section and the worker section, and the "N of M" counts match step 2.
4. Static checks: `grep -nE '(src|href)="https?:' <report>` finds nothing; `claude plugin validate .` passes (warnings that already existed are fine; record them); `python3 -m unittest discover tests` passes.

**Files it may change.** Only files under `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/02a/` and the progress notes. No repository files.

**Non-goals.** No code fixes. If something fails, record the observed output in the notes and return `blocked` or `partial` with the details. Do not run the interactive check. Do not touch `poe/poe-report-dashboard/`.

**Completion criteria.** The notes record, with observed output: the headless main transcript has non-empty thinking; the subagent transcript has non-empty thinking or, if not, its `display` value, flagged as a finding; the report shows them; the static checks pass.

**Progress notes.** `poe/poe-thinking-capture/progress/02a-validation.md`
