# Phase 01: docs edits (single unit)

Depends on: none. One unit; files tightly coupled (cross-references) → no parallel split.

## Unit 01a: SKILL.md + GRILLING.md + README.md

- Goal: implement `poe/analyse-grill/plan.md` Approach section exactly.
- Inputs / read:
  - `poe/analyse-grill/plan.md` (Approach, Assumptions, Decisions, Acceptance criteria)
  - `skills/poe/SKILL.md` (Plan step 2+4, Grill mode, Analyse mode)
  - `skills/poe/GRILLING.md`
  - `README.md` (Usage bullets, Analysis section)
  - `poe/docs/GLOSSARY.md` (use "analysis" per glossary)
- May change: `skills/poe/SKILL.md`, `skills/poe/GRILLING.md`, `README.md`. Nothing else.
- Edits:
  - SKILL.md Plan step 2: add `First analysis` to analysis-task field list.
  - SKILL.md Analyse step 1: no plan → open decisions → Grill mode with task, else one-shot plan; stop for review, `Next:` = `/poe:poe analyse <plan path>`. Plan exists but analysis fields missing → look up facts, grill remaining (GRILLING.md method, `## Decisions` appended), write fields into plan, continue.
  - SKILL.md Analyse step 3: first analysis = plan's `First analysis`; later = user's pick.
  - SKILL.md Grill step 5: `Next:` = analyse for analysis-only task; split for coding/mixed + one reply line that `analyse` works after.
  - GRILLING.md: short `## Analysis tasks` section: when it applies (data-analysis request, or entered from `analyse`); tree includes the five fields (question, data paths, notebook/output path, environment + `jupyter` call, first analysis); facts (data location, env, jupyter availability) looked up, not asked; fields already in plan not re-asked.
  - README: Grill + Analyse bullets and Analysis "Start" bullet match.
- Non-goals: no change to report script, phase-worker, catch-up/note, tests, plugin version/manifest. No new config. Keep each SKILL.md change to 1–2 lines; match existing terse style.
- Verify:
  ```sh
  grep -n "First analysis" skills/poe/SKILL.md skills/poe/GRILLING.md README.md
  grep -n -i "grill" skills/poe/SKILL.md | grep -i analys
  grep -n "Next:" skills/poe/SKILL.md
  grep -n -i "analyse <task>\|analyse <plan" README.md
  python3 -m pytest tests -q
  git diff --stat
  ```
  - Read-through: no remaining text says grill always ends with `split`, or that analyse no-plan never grills.
- Done when: all plan Acceptance criteria met; tests pass (observed); diff touches only the 3 allowed files.
- Progress notes: `poe/analyse-grill/progress/01a-docs.md`
