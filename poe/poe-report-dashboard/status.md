# Status: poe-report-dashboard

Plan: `poe/poe-report-dashboard/plan.md` — split approved (user ran `execute`, 2026-11-17). **All units verified; execution complete.** See `summary.md`.

| Phase | Unit | Description | Depends on | Status |
|---|---|---|---|---|
| 01 parser and docs | 01a | `poe_report.py` load + timeline, fixture, parsing tests | — | verified (15 tests OK; load_task on this task and on scratch 7234187e copy re-run by orchestrator) |
| 01 parser and docs | 01b | SKILL.md `report` mode + auto build, README | — | verified (diff reviewed; `claude plugin validate .` passed with pre-existing warnings) |
| 02 render | 02a | HTML rendering, `main()`, render tests | 01a | verified (29 tests OK; orchestrator re-ran report on scratch hello-txt: exit 0, no external refs, no `<script>`; missing dir exits 1) |
| 03 validation | 03a | Real transcripts, independent token sum, `/poe:poe report` headless | 01b, 02a | verified (independent checker re-run by orchestrator on e2e report: PASS) |

01a and 01b run in parallel (no shared files).

## Decisions

- Permission mode for the 03a headless run: **approved by the user 2026-11-17**: `--permission-mode acceptEdits --allowedTools "Bash(python3:*) Bash(mkdir:*) Bash(cp:*) Bash(find:*)"`, scratch dir only.
- The approved 03a command needs `--` before the prompt (`--allowedTools` takes a list). Permissions unchanged.
- Known from the previous task (`plans/poe-dir-and-logs/status.md`): the log-copy block can be denied in restrictive modes. Out of scope here; the report degrades to documents only.
- Usage is counted once per `message.id` per transcript (01a finding); `cost_usd` only on the main transcript, since `cost-state` covers workers too.
- 01b uses `${CLAUDE_SKILL_DIR}` (confirmed in the skills docs and the 2.1.326 binary); the command is in a new `## Report` section of SKILL.md.

## Next action

None. Open items for the user are listed in `summary.md` (browser check, token/cost note, commit).
