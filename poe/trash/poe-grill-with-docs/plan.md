# Plan: grill-with-docs in poe plan mode

## Objective
`/poe:poe plan` interviews user in rounds (Matt Pocock's grill-with-docs method) before writing plan.md. Resolved terms → `GLOSSARY.md`; qualifying decisions → ADRs; **every** resolved decision → plan.md. Fixes upstream's main gap ("other decisions live only in the conversation"): plan.md is the spec.

Upstream (MIT, © 2026 Matt Pocock, github.com/mattpocock/skills):
- `grill-with-docs/SKILL.md` = one-line shim calling the `grilling` + `domain-modeling` skills.
- `grilling`: design tree; ask the whole **frontier** (questions whose prerequisites are settled) per round; number questions, recommend an answer for each, word so "yes" accepts; then wait. Facts = agent's job (subagents); decisions = user's. Done when frontier empty + user confirms.
- `domain-modeling`: challenge terms vs glossary, sharpen fuzzy words, probe with edge-case scenarios, cross-check code; write `GLOSSARY.md` inline as each term resolves (no implementation detail); ADR only if hard to reverse **and** surprising **and** a real trade-off. Files created lazily.
- Known upstream bug: doc-writing silently skipped when run inside another orchestrator; deps sometimes not loaded.

## Decisions (made with user)
- Adapt method inline as a bundled poe file. No dependency on upstream skills.
- Grilling always on in plan mode. No flag, no new mode.
- `GLOSSARY.md` and `docs/adr/NNNN-slug.md` at cwd root (upstream layout), not in `poe/<slug>/`. Persist across tasks.

## Scope
In:
- **New `skills/poe/GRILLING.md`**: condensed adaptation of grilling + domain-modeling + glossary/ADR formats. Header: credit + link + MIT notice. Contents:
  - Rounds: frontier, numbered `Q1..Qn`, recommended answer each, "yes" = accept all, wait.
  - Facts via read-only subagents, not user; don't block the round on them.
  - Glossary: challenge/sharpen/scenarios/code cross-check; write term the moment it resolves; format (term, 1–2 sentence def, `_Avoid_:` synonyms); no implementation detail; `GLOSSARY-MAP.md` → use matching context's glossary.
  - ADR: 3 gates; format (title + 1–3 sentences; optional sections only if valuable); numbering = highest existing + 1.
  - Recommendations follow SKILL.md "do not overengineer" rules.
- **`skills/poe/SKILL.md`**:
  - Operating modes: plan mode may also create/edit `GLOSSARY.md` and `docs/adr/` at cwd root; still no implementation files.
  - Files section: note those two live outside `poe/`.
  - Plan mode rewritten:
    1. Inspect context, incl. existing `GLOSSARY.md`, `GLOSSARY-MAP.md`, `docs/adr/`.
    2. Read `${CLAUDE_SKILL_DIR}/GRILLING.md` now (explicit step; guards the not-loaded bug).
    3. Grill in rounds; stop after each round. Small/clear tasks may need one short round or none.
    4. After each answered round: append the decisions to `## Decisions` in plan.md (plan.md starts as decisions-only draft); write glossary/ADR changes inline. So nothing lives only in context; survives `/clear`.
    5. Frontier empty → ask user to confirm shared understanding.
    6. On confirm → write full plan.md (existing sections + `Decisions` + links to new ADRs / glossary terms). Existing don't-overengineer rules kept.
    7. Old step 4 ("ask before major architecture") folded into grilling.
    8. Review loop unchanged; a requested change that opens new decisions → short extra round.
    9. End reply with existing `Next:` split block (only after full plan written).
  - Split step 4: when `GLOSSARY.md` / relevant ADRs exist, list them in each unit's inputs.
- **`README.md`**: plan bullet describes grilling; Files section mentions `GLOSSARY.md`, `docs/adr/`; References credits mattpocock/skills.

Out:
- Upstream to-spec / wayfinder / other Matt skills.
- AskUserQuestion UI for rounds (4-question cap; text rounds per upstream).
- `phase-worker.md` changes (briefs carry the glossary path).
- `poe_report.py`, tests code, report format.
- Flags/config to disable grilling.
- Creating a GLOSSARY.md for this repo.

## Assumptions
- Builds on uncommitted `less_verboosity` edits to SKILL.md/README/phase-worker. Keep them.
- Logs copied once at end of plan mode (after full plan.md), not per round.
- Round format kept terse per Output style; recommended answers still required.
- cwd = where docs go, even if not repo root (matches poe's cwd rule).

## Acceptance criteria
- `skills/poe/GRILLING.md` exists, credits upstream with MIT notice, covers every item listed under Scope.
- SKILL.md plan mode tells the model to read GRILLING.md, grill in rounds, update `## Decisions` + glossary each round, confirm, then write plan.md.
- Split brief instructions mention glossary/ADR inputs.
- `claude plugin validate .` passes.
- `python3 -m unittest discover tests` passes (sanity; no code change).
- Manual run (below) shows: round format w/ recommendations; no full plan before confirm; facts looked up not asked; `GLOSSARY.md` changes mid-session (not one lump at end); Decisions section grows per round; ADRs only when gates met (zero is fine); final reply ends with `Next:` block.

## Risks
- Plan mode now multi-turn/slower. Mitigation: recommended answers, "yes" accepts round.
- Model skips GRILLING.md or batches doc writes at end (upstream bug). Mitigation: explicit read step, per-round write step; check in manual run.
- Writes outside `poe/` into user repo (surprise). Mitigation: lazy creation; README note.
- Glossary bloat with generic terms. Mitigation: upstream "project-specific only" rule kept.
- Round format fights concise-output rule. Mitigation: terse questions, required parts kept.
- License: condensed copy still credited + MIT notice.

## Validation
- `claude plugin validate .`
- `python3 -m unittest discover tests`
- Manual: scratch git repo w/ a few files; `claude --plugin-dir <this repo>`; `/poe:poe plan <toy task with fuzzy terms, e.g. "add archiving for old notes">`; answer 2–3 rounds (mix "yes" and overrides); check criteria above after each round (`git status`, `cat GLOSSARY.md`, `cat poe/<slug>/plan.md`). Then `/poe:poe split` → briefs list `GLOSSARY.md` in inputs.