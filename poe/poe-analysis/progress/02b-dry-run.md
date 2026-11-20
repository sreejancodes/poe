# 2b: status (done)

## Done so far
- Scratch dir: `D=/var/folders/kt/59ndz5693fb5hz_yj4xsnstj1m0z31/T/tmp.N9QrUTmYei`
- Env: `/Users/sbandyopadhyay/miniforge3/envs/data_analysis/bin/jupyter`, kernel `python3` -> env python (abs path in kernel.json), pandas 2.3.3. OK.
- Step 1 PASS: `$D` git init + scratch commit `init` (data/toy.csv 20 rows, poe/toy/plan.md: question, data, paths, env).
- Step 2 PASS: acted as worker x2. Notebook `notebooks/toy/toy.ipynb` created (01), appended (02); both nbconvert runs rc=0, 0 error outputs. Records `poe/toy/analysis/01-dose-response.md`, `02-group-slopes.md`; 2 log entries `By: poe`. Results: pooled slope 0.735 r=0.862; slope A=0.98 B=0.49 (`notebooks/toy/group_slopes.csv`).
- Step 3 PASS: hand-added untagged code cell (group means), executed. Catch-up scan #1 (scratchpad script `catchup_scan.py`, json only) found group `[5]` with src+output; drafted `manual` entry "Mean response by group" (A=3.01, B=2.03). **User confirmation simulated** (accepted draft as-is). Appended; cell 5 tagged `poe:manual`. Scan #2: nothing found. Notebook still valid.
- Step 4 PASS: note-mode entry appended in "user's words" (`Checked raw CSV by eye in Excel; no outliers in group B`), `[manual]`, `By: user`. No untagged cells left to tag. Log copy not tested (no session id in scratch).
- Step 5 PASS (with gap): dummy `poe/toy/phases/01-x.md`, `poe/toy/progress/01a-x.md`; `python3 .../skills/poe/scripts/poe_report.py poe/toy` rc=0 -> `poe/toy/report.html` (8135 B). Contains both records (01, 02 text incl. results) + phase/progress docs + plan.md. Does NOT contain ANALYSIS_LOG entries (manual/note invisible in report).
- Untested: interactive `AskUserQuestion` loop (Analyse step 5), catch-up confirm/fix dialog (simulated), Logs copy step, `analyse catch-up` arg resolution, orchestrator `status.md` update.

## Files changed or produced
- Repo: this notes file only (repo `git status` same as session start).
- `$D`: data/toy.csv, poe/toy/plan.md, notebooks/toy/{toy.ipynb,group_slopes.csv}, poe/toy/analysis/{01-dose-response,02-group-slopes}.md, poe/docs/ANALYSIS_LOG.md, poe/toy/phases/01-x.md, poe/toy/progress/01a-x.md, poe/toy/report.html
- Scratchpad helpers: `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/19af2295-22b3-4590-b048-5a17141b4c60/scratchpad/{add01.py,add02.py,catchup_scan.py}`

## Tests run and observed results
Brief verify commands, run in `$D`:
- tags: `[['poe:toy/01'], ['poe:toy/01'], ['poe:toy/01'], ['poe:toy/02'], ['poe:toy/02'], ['poe:manual']]`
- `ls poe/toy/analysis` -> `01-dose-response.md 02-group-slopes.md` (2 records); `grep -c '^## ' poe/docs/ANALYSIS_LOG.md` -> `4` (4 entries)
- `grep -c 'analysis/0' poe/toy/report.html` -> `3` (>=2)
- extra: `grep -c '"output_type": "error"' notebooks/toy/toy.ipynb` -> `0`; git status before 02: `?? notebooks/toy/toy.ipynb`
- extra report greps: `Mean response by group` 0, `outliers in group B` 0, `ANALYSIS_LOG` 0.

## Decisions and assumptions
- Scratch commit in `$D` only (not repo) so git status checks mean something.
- Cells written via nbformat with env python; notebook reads `../../data/toy.csv` (nbconvert cwd = notebook dir).
- Log `Follows:` first analysis = `none`; manual/note = `toy/02` (latest). Anchor = GitHub-style heading slug.
- Catch-up scanned `notebooks/` recursively ("plan's path" interpreted as dir of plan's notebook path); "notebook with no record" = notebook path not string-present in any `analysis/*.md`.
- Catch-up entry `By: user` (cell by user, wording by poe).

## Defects / ambiguities found (not fixed)
1. phase-worker.md "Default: append to the task's existing notebook" / "Cells: append to the given notebook": nothing for first analysis when notebook absent (create? kernelspec? title cell?). Created it.
2. phase-worker.md "Before executing: run `git status --porcelain -- <nb>` and compare the file with what you read. ... Uncommitted changes from before → execute, but warn that the user may have the notebook open": (a) workers never commit, so from analysis 02 on notebook is always `??`/` M` from poe's own prior write -> warning every run, noise; (b) check placed "before executing", i.e. after worker already appended cells, so "compare with what you read" really must happen before writing cells; order unclear.
3. Record format `## Next  options proposed; option chosen` (SKILL.md Analysis record + phase-worker.md): worker writes record, user chooses after worker returns (Analyse step 5 "ask next analysis via AskUserQuestion"); no step says who fills "option chosen". Step 5 only says "update `status.md`".
4. Log format `- Follows: <slug>/NN`: no value for first analysis, nor for `manual`/note entries. `- Links: record, notebook#heading`: anchor format unspecified. `[<slug>/NN | manual]`: manual entries carry no task slug, so project-wide log cannot attribute them to a task.
5. Catch-up "Scan notebooks under the plan's path for untagged code cells (and notebooks with no record)": plan.md has no single "path" field (Analyse step 1: "question, data, paths, environment"); and nothing says what to do with a notebook with no record (draft one entry for whole notebook?).
6. Catch-up / Note mode "Tag cells `poe:manual`": orchestrator edits notebook with no git-status/open-in-Jupyter check (unlike worker rule); user saving an open notebook drops the tag -> re-asked next catch-up.
7. Note mode "Append `manual` log entry in user's words": which field holds the words unspecified (heading `<question>` vs `Result`); I put them in both.
8. Report: `poe_report.py` (`TASK_DOCUMENT_FOLDERS = ["phases", "progress", "analysis"]`) ignores `poe/docs/ANALYSIS_LOG.md`, so manual/note entries never reach `report.html`. Consistent with plan ("render `analysis/` records") but untracked work is invisible in report; flag for user.
9. SKILL.md Notebook rules "Execute headless: `jupyter nbconvert ...`, in the plan's environment; `jupyter` missing → report and stop": literal `jupyter` not on PATH here; works only if plan.md names env jupyter path (did so). Worth saying plan's Environment must give jupyter path/activation.

## Next step / remaining work
- None for 2b. Orchestrator: triage defects 1–9 (fix in SKILL.md/phase-worker.md or accept).
