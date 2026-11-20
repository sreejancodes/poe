# Phase 01: results page

Depends on: nothing. Units 01a and 01b run in parallel (no shared files).

## Shared interface (both units rely on it; do not change)

- Command: `python3 "${CLAUDE_SKILL_DIR}/scripts/poe_results.py" [session-dir]` (default `.`).
- Writes `<session-dir>/poe/docs/all_analysis.html` (creates `poe/docs/` if absent), overwrites every run, prints the path, exit 0 (also when no log / no analyses).
- Inputs: `poe/docs/ANALYSIS_LOG.md` + `poe/<slug>/analysis/NN-*.md` for every slug except `docs`, `trash`.
- Figure/table paths in records (`## Result`) and log `Links:` are relative to session dir; plain, in backticks, or as markdown links `[x](path)` all accepted.
- Untracked (`manual`) entry placement: `Follows: <slug>/NN` → under that analysis; else its notebook path matches (same file, else same directory) a notebook named in a task's records → that task's section; else "Untracked work" section.

## Unit 01a: script + tests

- Goal: implement `skills/poe/scripts/poe_results.py` per plan Assumptions/Approach + shared interface; fixture + tests.
- Inputs: `poe/all-analysis-html/plan.md` (Decisions, Assumptions, Acceptance criteria), this brief, `skills/poe/SKILL.md` sections "Analysis record" + "Analysis log entry" (formats parsed), `skills/poe/scripts/poe_report.py` (style: stdlib, dataclasses, Load/Arrange/Render, defensive parsing, inline CSS, light/dark), `tests/test_poe_report.py` (test style), `poe/docs/GLOSSARY.md`.
- May change: `skills/poe/scripts/poe_results.py` (new), `tests/test_poe_results.py` (new), `tests/fixtures/results/` (new fixture session dir: `poe/docs/ANALYSIS_LOG.md`, 2 tasks with records incl. a Follows chain, one failed/abandoned record, one existing small PNG figure, one missing figure, one manual entry with Follows, one manual entry placed by notebook, one manual entry in fallback, one malformed entry).
- Non-goals: no edits to `poe_report.py`, SKILL.md, README, phase-worker.md; no JS, no base64 images, no dates on page, no third-party deps.
- Verify:
  - `python3 -m unittest discover tests` → all pass (old + new).
  - `python3 skills/poe/scripts/poe_results.py tests/fixtures/results` → prints path; run twice, `shasum` identical.
  - `python3 skills/poe/scripts/poe_results.py <empty tmp dir in scratchpad>` → exit 0, empty-state page.
  - Generated fixture HTML: do not commit; add `tests/fixtures/results/poe/docs/all_analysis.html` to `.gitignore` only if tests write there, else have tests write to a temp copy (preferred: temp copy, no `.gitignore` change).
- Done when: every Acceptance-criteria bullet about the script has a passing test (task sections, nested thread, inline img, missing marker, manual under Follows, manual by notebook, fallback section, latest marked, dimmed failed/abandoned, skipped count in footer, byte-identical rerun, empty dir).
- Progress notes: `poe/all-analysis-html/progress/01a-script.md`.

## Unit 01b: docs

- Goal: document results page in SKILL.md, README, phase-worker.
- Inputs: `poe/all-analysis-html/plan.md`, this brief (shared interface), `skills/poe/SKILL.md`, `README.md`, `agents/phase-worker.md`, `poe/docs/GLOSSARY.md`.
- May change: `skills/poe/SKILL.md`, `README.md`, `agents/phase-worker.md`.
- Edits:
  - SKILL.md Operating modes: add `results`: run script, reply path only (+ failure); may write only `poe/docs/all_analysis.html`.
  - SKILL.md Files: `poe/docs/all_analysis.html` = results page (project-wide, script-built).
  - SKILL.md: add short "Results page" section with the command (as Report section); failure → say so, never blocks.
  - SKILL.md Analyse step 5, Note mode, Catch-up check: rebuild results page after log write.
  - SKILL.md Note mode + Catch-up: fill `Follows: <slug>/NN` when cells sit after a poe-tagged group or user names it.
  - SKILL.md Logs list of modes: include `results`.
  - phase-worker.md Analysis units: figure/table paths in `## Result` relative to session dir.
  - README: results page + `results` mode, near report docs; scripts list adds `poe_results.py`.
- Non-goals: no script/test edits; keep SKILL.md terse (Output style); no restating plan.
- Verify: `grep -n "all_analysis.html\|poe_results.py\|results" skills/poe/SKILL.md README.md agents/phase-worker.md` shows each edit; `git diff --stat` touches only the 3 allowed files.
- Done when: every Edits bullet present; wording consistent with GLOSSARY "Results page".
- Progress notes: `poe/all-analysis-html/progress/01b-docs.md`.
