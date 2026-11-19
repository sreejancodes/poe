# Plan: `grill` mode for poe

## Objective
New mode `/poe:poe grill <task | plan-path>`: interview user in rounds (Matt Pocock's grill-with-docs method) until design tree resolved, then write same `plan.md` as plan mode. Maintains `poe/GLOSSARY.md` + `poe/docs/adr/` inline. `plan` mode unchanged.

Upstream (MIT, © 2026 Matt Pocock, github.com/mattpocock/skills); research in `poe/trash/poe-grill-with-docs/plan.md`:
- `grilling`: per round ask whole frontier (questions w/ settled prereqs); numbered, recommended answer each, "yes" = accept all; wait. Facts = agent looks up; decisions = user.
- `domain-modeling`: sharpen terms, edge-case scenarios, code cross-check; glossary written as each term resolves; ADR only if hard to reverse + surprising + real trade-off.
- Upstream gap: non-ADR decisions live only in chat → fix: all decisions → `plan.md` `## Decisions` each round.

## Grill vs plan
| | `plan` | `grill` |
|---|---|---|
| Turns | 1 + review | many rounds, then plan |
| Decides | agent assumes, user corrects | user decides, agent recommends |
| Fits | clear/small tasks | fuzzy scope, trade-offs, costly rework |
| Output | `plan.md` | + `## Decisions`, glossary, ADRs |
| Cost | fast | slower, more attention + context |
| Fails by | hidden assumptions | fatigue, trivia, bikeshedding |

## Decisions
- Separate `grill` mode; `plan` untouched.
- Method inline in bundled `skills/poe/GRILLING.md`; no upstream dependency.
- Shared docs at `poe/GLOSSARY.md` + `poe/docs/adr/NNNN-slug.md` (poe root, not task slug). Created lazily, shared across tasks.
- Slug `docs` reserved (collides w/ `poe/docs/`).
- Rounds as plain text, not AskUserQuestion (4-question cap).

## Scope
In:
- **New `skills/poe/GRILLING.md`**: credit + link + MIT notice. Rounds rules; facts via code/read-only subagents; recommendations obey "do not overengineer"; glossary format (term, 1–2 sentence def, `_Avoid_:` synonyms; project terms only; no impl detail); ADR 3 gates + format, number = highest + 1; skip trivia, small task may need 1 round.
- **`skills/poe/SKILL.md`**:
  - `argument-hint` + Operating modes: add `grill <task | plan-path>`; may write `poe/GLOSSARY.md`, `poe/docs/adr/`; no impl files.
  - Files: show `poe/GLOSSARY.md`, `poe/docs/adr/` beside task dirs; never use slug `docs`.
  - New Grill mode section:
    1. Plan step 1 + read `poe/GLOSSARY.md`, `poe/docs/adr/`, `${CLAUDE_SKILL_DIR}/GRILLING.md`.
    2. Arg = existing `plan.md` → load + grill only open/risky points. Else new slug, `plan.md` w/ only `## Decisions`.
    3. Each round: ask, stop. After answers: append `## Decisions`, write glossary/ADR now.
    4. Frontier empty → confirm shared understanding.
    5. On confirm → full plan per Plan steps 2–4 (keep Decisions, link ADRs), then Plan step 5 reply.
    6. Copy logs at end.
  - Split step 4: list `poe/GLOSSARY.md` / relevant ADRs in unit inputs when present.
- **`README.md`**: grill usage + 1–2 lines grill vs plan; Files tree adds shared docs; gitignore note: ignore `poe/*/logs/` + `poe/*/report.html`, not all of `poe/`, to keep glossary/ADRs; credit upstream.

Out:
- `plan` mode behavior, `phase-worker.md`, `poe_report.py`, tests, flags, glossary in report.

## Assumptions
- Keep uncommitted `less_verboosity` edits.
- Round questions terse; recommendation per question always kept.
- `poe/` relative to cwd (existing rule).

## Acceptance criteria
- `GRILLING.md` exists, credited w/ MIT notice, covers Scope items.
- SKILL.md: `grill` in argument-hint + modes; Grill section steps 1–6; reuses Plan steps by reference; Plan section unchanged; `docs` slug reserved.
- Split step 4 mentions glossary/ADR inputs.
- `claude plugin validate .` passes.
- `python3 -m unittest discover tests` passes.
- Manual: numbered rounds w/ recommendations; no full plan before confirm; facts not asked; `## Decisions` grows per round; `poe/GLOSSARY.md` written mid-session; ADRs only when gated (zero ok); ends w/ `Next:` block; `grill <plan.md>` after `/clear` doesn't re-ask settled points; nothing written outside `poe/`.

## Risks
- Fatigue / trivia → recommendations, "yes" accepts, skip-trivia rule.
- Docs written only at end (upstream bug) → explicit per-round write step.
- User ignores all of `poe/` in git → glossary/ADRs lost from history; README note.
- Upstream skills/tools expect root `GLOSSARY.md` → won't find poe's; accepted.
- Parent context grows over rounds → Decisions on disk; `/clear` + `grill <plan-path>`.
- Plan/grill drift → reference, don't copy.

## Validation
- `claude plugin validate .`
- `python3 -m unittest discover tests`
- Manual: scratch git repo; `claude --plugin-dir <this repo>`; `/poe:poe grill <fuzzy task, e.g. "add archiving for old notes">`; 2–3 rounds (mix "yes"/overrides); each round: `git status`, `cat poe/GLOSSARY.md`, `cat poe/<slug>/plan.md`. `/clear` → `/poe:poe grill poe/<slug>/plan.md` → no re-asks. `/poe:poe plan <same task>` → one-shot. `split` → briefs list `poe/GLOSSARY.md`.
