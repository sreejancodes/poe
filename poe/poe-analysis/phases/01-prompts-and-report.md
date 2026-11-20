# Phase 01: prompts and report

Depends on: nothing. Units 1a, 1b, 1c run in parallel (no shared files).

Common inputs (all units): `poe/poe-analysis/plan.md` (source of truth for formats: analysis record, log entry, notebook rules, catch-up, `note`), `poe/docs/GLOSSARY.md`.
Common rules: terms per glossary ("analysis", never "analysis step"; "untracked work"). Match existing terse style of each file. No commit.

## Unit 1a: SKILL.md

- Goal: document analysis support in `skills/poe/SKILL.md`.
- Read: `skills/poe/SKILL.md` (has uncommitted user edits: preserve).
- May change: `skills/poe/SKILL.md` only.
- Do:
  - Operating modes: add `analyse [task | plan-path]`, `analyse catch-up`, `note <text>`; state which files each may write.
  - Files tree: add `poe/docs/ANALYSIS_LOG.md`, `poe/<slug>/analysis/NN-name.md`; notebooks/outputs live in project path named in `plan.md`.
  - Plan mode: analysis task's `plan.md` adds question, data paths, notebook/output path, environment (incl. how to call `jupyter`).
  - New section "Analyse mode": steps 1–6 of plan "### `analyse`", incl. switch to/from `plan`/`split`/`execute` on same task dir, loop end (summary, logs, report), next-analysis via `AskUserQuestion`.
  - New sections: analysis record format, log entry format, notebook rules, catch-up check, note mode: as in plan, verbatim formats.
  - Split/Execute: analysis units (brief gains notebook path + record path; worker writes record + log entry; log-writing units sequential).
  - Resume: task with analyses → read `status.md` + latest record, continue loop.
  - Logs section: add `analyse`, `note` to list of modes that copy logs.
- Non-goals: no change to GRILLING.md, README, worker, script; no rewrite of existing modes beyond the above.
- Verify:
  - `grep -n "analyse\|note <text>\|ANALYSIS_LOG\|catch-up\|poe:manual" skills/poe/SKILL.md` → all present.
  - `grep -n -i "analysis step" skills/poe/SKILL.md` → none.
  - `git diff skills/poe/SKILL.md` → pre-existing uncommitted edits intact, existing modes unchanged in meaning.
- Done when: every Scope bullet for SKILL.md in plan is covered; formats match plan exactly.
- Progress notes: `poe/poe-analysis/progress/01a-skill-md.md`

## Unit 1b: phase-worker.md

- Goal: worker rules for an analysis unit.
- Read: `agents/phase-worker.md`.
- May change: `agents/phase-worker.md` only.
- Do: add short section "Analysis units", applied when brief gives a notebook path:
  - Append cells under markdown heading `## NN: <question>` in the given notebook; tag every cell written with `poe:<slug>/<NN>` in cell metadata `tags`.
  - Notebook rules from plan (fewest files; new notebook only if full re-run > ~5 min or topic change, save intermediates, state reason in record; no dead cells).
  - Before executing: check notebook not modified/unsaved elsewhere (git status); warn rather than overwrite.
  - Execute headless: `jupyter nbconvert --to notebook --execute --inplace <nb>` using the environment named in the plan; `jupyter` missing → report and stop.
  - Write analysis record (plan format) at given path; append one entry to `poe/docs/ANALYSIS_LOG.md` (plan format; create file with `# Analysis log` heading if absent).
  - Return ≤5 bullets + 2–3 proposed next analyses.
- Non-goals: no change to existing numbered rules beyond what is needed; no frontmatter change.
- Verify:
  - `grep -n "nbconvert\|ANALYSIS_LOG\|tags\|Analysis units" agents/phase-worker.md` → all present.
  - `head -5 agents/phase-worker.md` → frontmatter unchanged.
- Done when: a worker given only brief + this file could do an analysis unit per plan.
- Progress notes: `poe/poe-analysis/progress/01b-phase-worker.md`

## Unit 1c: report script

- Goal: `report.html` shows `analysis/*.md` records as text.
- Read: `skills/poe/scripts/poe_report.py` (lines ~40–125: `TASK_DOCUMENT_FOLDERS`, `load_documents`; `render_documents`), `tests/test_poe_report.py` (existing document tests).
- May change: `skills/poe/scripts/poe_report.py`, `tests/test_poe_report.py`, `tests/fixtures/` (only if a fixture is needed).
- Do: add `"analysis"` to `TASK_DOCUMENT_FOLDERS`; update module docstring/comments if they list folders; add a unittest that a task dir with `analysis/01-x.md` yields document `analysis/01-x.md` in the rendered report, in file order.
- Non-goals: no embedding of figures/notebooks; no link rewriting; no notebook parsing; stdlib only.
- Verify: `python3 -m unittest discover tests` → all pass (baseline before change: 40 tests OK); pytest is not installed.
- Done when: new test passes, old 40 pass.
- Progress notes: `poe/poe-analysis/progress/01c-report.md`
