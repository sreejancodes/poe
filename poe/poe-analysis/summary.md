# Summary: poe-analysis (execute, 2026-11-20)

## Passed
- All 5 units verified (see `status.md`).
- `python3 -m unittest discover tests` → 41 OK (baseline 40 + new analysis test).
- Dry run (toy data, scratch `/var/folders/kt/59ndz5693fb5hz_yj4xsnstj1m0z31/T/tmp.N9QrUTmYei`): 1 notebook, tags `[toy/01 ×3, toy/02 ×2, manual]`, 0 error outputs, 2 records, 4 log entries, catch-up re-run finds nothing, `report.html` has records + phase docs.
- Pre-existing uncommitted edits in `SKILL.md`, `README.md` intact (checked vs pre-execute snapshot).

## Changed files
- `skills/poe/SKILL.md`: modes `analyse`, `analyse catch-up`, `note`; Files tree; plan fields; Analyse mode; record/log formats; notebook rules; catch-up; note mode; split/execute/resume/logs hooks.
- `agents/phase-worker.md`: "Analysis units" section.
- `skills/poe/scripts/poe_report.py`: `analysis` in `TASK_DOCUMENT_FOLDERS`.
- `tests/test_poe_report.py`: `test_analysis_records_listed_and_rendered_in_file_order`.
- `README.md`: modes, examples, Analysis section, file tree.

## Orchestrator fixes after dry run (findings in `progress/02b-dry-run.md`)
- Worker creates notebook if absent.
- Pre-execute check: mtime noted before writing cells; stop only if saved by someone else meanwhile (was: git-status warning every run).
- Orchestrator writes chosen option into record `## Next`.
- `Follows: -` when none.
- Catch-up scans plan's notebook/output path; notebook with no tagged cells = one group.
- `note`: user text as `<question>`, `Result` only if stated.

## Uncertain / open (user decision)
- Finding 6: catch-up/`note` tag cells without open-notebook check → user saving open notebook can drop tag → re-asked.
- Finding 8: `report.html` ignores `poe/docs/ANALYSIS_LOG.md` → manual/note work not in report (matches plan; flag).
- Finding 4: `manual` log entries carry no task slug; `notebook#heading` anchor format undefined.
- Untested: interactive `AskUserQuestion` loop, catch-up confirm dialog (simulated), `status.md` update in analyse loop. Needs a real `/poe:poe analyse` session.

## Not done
- No commit.
