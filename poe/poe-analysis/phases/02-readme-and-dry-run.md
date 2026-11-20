# Phase 02: README and dry run

Depends on: phase 01 verified. Units 2a, 2b run in parallel (no shared files).

Common inputs: `poe/poe-analysis/plan.md`, `poe/docs/GLOSSARY.md`, `skills/poe/SKILL.md` (as changed by 1a).

## Unit 2a: README

- Goal: document analysis support for users.
- Read: `README.md` (has uncommitted user edits: preserve), `skills/poe/SKILL.md`.
- May change: `README.md` only.
- Do: add `analyse`, `analyse catch-up`, `note` to mode list/examples; short section on analysis workflow (one task for coding + analysis, notebook rules, analysis records, `poe/docs/ANALYSIS_LOG.md`, untracked work); update file tree if README has one; note `jupyter` requirement.
- Non-goals: no change to SKILL.md; no restating of full formats (point to SKILL.md).
- Verify: `grep -n "analyse\|note\|ANALYSIS_LOG" README.md` → present; `git diff README.md` → earlier edits intact; README claims match SKILL.md.
- Done when: a new user could start an analysis task from README alone.
- Progress notes: `poe/poe-analysis/progress/02a-readme.md`

## Unit 2b: dry run

- Goal: check the documented mechanics work end to end on a toy dataset.
- Read: `skills/poe/SKILL.md`, `agents/phase-worker.md`.
- May change: only files under a new scratch dir `D=$(mktemp -d)`; nothing in the repo except its progress notes. Defects found in SKILL.md / phase-worker.md / script → record in notes, do not fix.
- Environment: `jupyter` not on PATH; use `/Users/sbandyopadhyay/miniforge3/envs/data_analysis/bin/jupyter`. Missing kernel/packages → report, stop.
- Do, in `$D`, acting as the analysis worker described in `agents/phase-worker.md` (cannot invoke `/poe:poe`; follow the text by hand):
  1. `git init`; toy CSV (~20 rows); `poe/toy/plan.md` with question, data path, notebook path `notebooks/toy/toy.ipynb`.
  2. Analysis 01 and 02 per worker rules → one notebook, 2 headed + tagged sections, executes clean; `poe/toy/analysis/01-*.md`, `02-*.md`; 2 entries in `poe/docs/ANALYSIS_LOG.md`.
  3. Hand-add one untagged code cell; run catch-up as SKILL.md describes → cell found, `manual` entry drafted and appended (user confirmation simulated; say so), cell tagged `poe:manual`; second catch-up finds nothing.
  4. `note`-mode entry appended per SKILL.md.
  5. Add a dummy `phases/01-x.md` + `progress/01a-x.md`; run `python3 /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe/skills/poe/scripts/poe_report.py poe/toy` → `report.html` contains both analysis records and phase docs.
- Non-goals: no real data; no changes to implementation files; no test of the interactive `AskUserQuestion` loop (cannot be run by a worker: state as untested).
- Verify (print outputs into notes):
  - `python3 -c "import json;nb=json.load(open('notebooks/toy/toy.ipynb'));print([c['metadata'].get('tags') for c in nb['cells']])"`
  - `ls poe/toy/analysis; grep -c '^## ' poe/docs/ANALYSIS_LOG.md` → 2 records; 4 entries.
  - `grep -c 'analysis/0' poe/toy/report.html` → ≥2.
- Done when: all 5 steps observed, or each failure recorded with the instruction text that was ambiguous or wrong.
- Progress notes: `poe/poe-analysis/progress/02b-dry-run.md`
