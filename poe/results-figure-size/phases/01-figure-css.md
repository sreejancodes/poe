# Phase 01: figure CSS cap + wrap

Depends on: none. One unit.

## Unit 01a: cap figure size, wrap figures

- Goal: results page figures capped (≤7.2in wide, ≤3.5in tall, no upscaling) and an analysis's figures wrap side by side; per `poe/results-figure-size/plan.md` Approach.
- Inputs:
  - `poe/results-figure-size/plan.md` (Decisions, Approach, Acceptance criteria)
  - `skills/poe/scripts/poe_results.py`: CSS block (~L430–475, `figure`/`figure img` rules), `render_figure` (~L709), `render_analysis` (~L720–745)
  - `tests/test_poe_results.py`, `tests/fixtures/results/`
  - `poe/docs/GLOSSARY.md` (term: Results page)
- May change: `skills/poe/scripts/poe_results.py`, `tests/test_poe_results.py`, `tests/fixtures/results/**` only if a 2-figure analysis fixture is needed.
- Non-goals: `poe_report.py`; SKILL.md / phase-worker.md; JS/lightbox; reading image dpi; resizing figure files; other CSS.
- Steps:
  - `render_analysis`: wrap figures in `<div class="figures">…</div>` only when ≥1 figure.
  - CSS: `.figures { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: flex-start; }`; `figure { margin: 8px 0; max-width: 100%; }`; `figure img { max-width: min(100%, 7.2in); max-height: 3.5in; width: auto; height: auto; ... }` keep border/radius/bg.
  - Tests: cap strings in output; figures inside `<div class="figures">`; analysis without figures → no empty wrapper; rerun byte-identical (existing test if present).
- Verify:
  - `python3 -m unittest discover tests`
  - `python3 skills/poe/scripts/poe_results.py tests/fixtures/results` → prints page path; `grep -c 'class="figures"' <page>`; `grep -n 'max-height: 3.5in' <page>`
  - `git diff --stat` touches only allowed files
- Done when: all tests pass (observed), acceptance criteria 1–3 in plan.md met, progress notes `done`.
- Progress notes: `poe/results-figure-size/progress/01a-figure-css.md`
- Manual check (user, after unit): rebuild on project with oversized barplot; light + dark; narrow window.
