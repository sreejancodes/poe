# Phase 01: write GRILLING.md, SKILL.md, README.md

- Depends on: approved `plan.md`.
- Units 01a, 01b, 01c touch disjoint files → run in parallel.
- Shared contract: method file path is `skills/poe/GRILLING.md`; SKILL.md loads it via `${CLAUDE_SKILL_DIR}/GRILLING.md`; shared docs at `poe/docs/GLOSSARY.md`, `poe/docs/adr/NNNN-slug.md`; decisions go to `plan.md` `## Decisions`.
- All units: follow SKILL.md Output style (terse); no new features beyond plan; check `git status` before edits; no commits.

## Unit 01a: GRILLING.md
- Goal: write new `skills/poe/GRILLING.md`, the bundled grilling + domain-modeling method.
- Read: `poe/poe-grill/plan.md` (Objective, Decisions, Scope → GRILLING.md bullets); `poe/trash/poe-grill-with-docs/plan.md` (upstream research); `skills/poe/SKILL.md` Output style + "do not overengineer" (Plan step 3) for tone/rules.
- May change: `skills/poe/GRILLING.md` (new) only.
- Must cover: credit Matt Pocock + link github.com/mattpocock/skills + MIT notice (© 2026 Matt Pocock); round rules (frontier, numbered Q1..Qn, recommended answer each, "yes" accepts all, override by number, then stop; plain text, no AskUserQuestion); facts looked up in code / read-only subagents, never asked; recommendations follow do-not-overengineer; skip trivia, clear task may need one round or none; glossary format (term, 1–2 sentence definition, `_Avoid_:` synonyms; project terms only, no impl detail; created only when first needed); 3 ADR conditions (hard to reverse, surprising, real trade-off) + ADR format + numbering = highest existing + 1; write after every answered round (append `## Decisions` in plan.md, update glossary/ADRs); finish when frontier empty and user confirms shared understanding.
- Non-goals: SKILL.md, README, scripts, tests; copying upstream text verbatim beyond what the notice covers.
- Verify:
  - `test -f skills/poe/GRILLING.md && grep -n -i -e "MIT" -e "mattpocock" -e "_Avoid_" -e "frontier" -e "Decisions" skills/poe/GRILLING.md`
  - Manual read-through against the "Must cover" list.
- Done when: every "Must cover" item present; file terse.
- Progress notes: `poe/poe-grill/progress/01a-grilling-md.md`

## Unit 01b: SKILL.md
- Goal: add Grill mode + plan→grill routing + docs rules to `skills/poe/SKILL.md`.
- Read: `poe/poe-grill/plan.md` (Decisions, Scope → SKILL.md bullets); `skills/poe/SKILL.md`.
- May change: `skills/poe/SKILL.md` only.
- Changes:
  - frontmatter `argument-hint` + Operating modes: `grill <task | plan-path>`; may write `poe/<slug>/plan.md`, `poe/docs/GLOSSARY.md`, `poe/docs/adr/`; never implementation files.
  - Files: show `poe/docs/` beside task dirs; slug `docs` reserved; `poe/docs/` and `poe/trash/` never the "active plan" for path-less modes.
  - Plan step 1: also read `poe/docs/` if present. Plan step 4 replaced: open decisions (user's to make, not settleable from code/defaults) → switch to Grill mode with the task; else one-shot.
  - New "Grill mode" section, steps 1–6 exactly as plan Scope; point to Plan steps, don't copy them; reads `${CLAUDE_SKILL_DIR}/GRILLING.md`; ends with Plan step 5 reply (`Next:` split block); logs copied at end.
  - Logs section: list `grill` among modes that copy logs.
  - Split step 4: when `poe/docs/GLOSSARY.md` or relevant ADRs exist, list them in each unit's inputs.
- Non-goals: rewording unrelated sections; Execute/Resume/Report changes; GRILLING.md content.
- Verify:
  - `grep -n -e "grill" -e "poe/docs" -e "GRILLING.md" skills/poe/SKILL.md`
  - `head -10 skills/poe/SKILL.md` (frontmatter valid YAML, argument-hint includes grill)
  - `claude plugin validate .`
- Done when: all Changes present; validate passes (output observed).
- Progress notes: `poe/poe-grill/progress/01b-skill-md.md`

## Unit 01c: README.md
- Goal: document `grill` in `README.md`.
- Read: `poe/poe-grill/plan.md` (Scope → README bullet); `README.md`.
- May change: `README.md` only.
- Changes: `grill` usage (`grill <task>`, `grill <plan-path>`); 1–2 lines plan vs grill (plan = clear task, auto-switches to grill on open decisions; grill = explicit interview / refine draft); `poe/docs/` (GLOSSARY.md, adr/) in Files tree; gitignore advice → ignore `poe/*/logs/` and `poe/*/report.html`, not all of `poe/`; credit upstream (Matt Pocock, github.com/mattpocock/skills, MIT) under References.
- Non-goals: rewriting other README sections.
- Verify: `grep -n -e "grill" -e "poe/docs" -e "poe/\*/logs" -e "mattpocock" README.md`
- Done when: all Changes present.
- Progress notes: `poe/poe-grill/progress/01c-readme.md`
