# Plan: `grill` mode for poe

## Objective
Add the interview method from Matt Pocock's grill-with-docs to poe. `plan` stays the fast one-shot path. The new `grill` mode either questions the user from scratch or refines an existing `plan.md`. `plan` hands off to grilling on its own when the request is fuzzy. Terms and hard decisions are saved in shared docs under `poe/docs/` so later tasks can reuse them.

Upstream (MIT, © 2026 Matt Pocock, github.com/mattpocock/skills); earlier research is in `poe/trash/poe-grill-with-docs/plan.md`:
- `grilling`: build a tree of design decisions. Each round asks the whole **frontier** (the questions whose prerequisites are already settled), numbered, with a recommended answer for each; "yes" accepts them all; then wait. The agent looks up facts itself; the user makes decisions.
- `domain-modeling`: sharpen fuzzy terms, probe edge cases, check the code; write each glossary entry as soon as the term is resolved; write an ADR only if the decision is hard to reverse, surprising, and a real trade-off.
- Gap in upstream: decisions that don't qualify for an ADR stay only in the chat. Fix: every decision goes into `plan.md` under `## Decisions`, every round.

## Decisions (made with user)
- `grill` is a separate mode, with two entry points:
  - `grill <task>`: question the user from scratch, then write the full `plan.md`.
  - `grill <plan-path>`: question the user only on that plan's assumptions and open or risky points, then update the plan in place. This counters a draft that anchored on wrong assumptions.
- `plan` stays one-shot for clear tasks. If it finds open decisions it cannot settle from the code or sensible defaults, it switches to the grill flow instead of guessing. This replaces Plan step 4 ("ask before major architecture").
- Shared docs live at the poe root and are reused across tasks: `poe/docs/GLOSSARY.md` and `poe/docs/adr/NNNN-slug.md`. Both are created only when first needed.
- Rounds are plain text (Q1..Qn, each with a recommended answer; reply "yes" or override by number). AskUserQuestion is not used.
- The method is written into a bundled `skills/poe/GRILLING.md`; poe does not depend on the upstream skills.

## Scope
In:
- **New `skills/poe/GRILLING.md`**: credit + link + MIT notice. Covers:
  - Round rules: ask the frontier, numbered questions, a recommended answer for each, "yes" accepts all, then stop.
  - Look up facts in the code or with read-only subagents; never ask the user for them.
  - Recommendations follow the "do not overengineer" rules. Skip trivia; a clear task may need one round or none.
  - Glossary format: term, 1–2 sentence definition, `_Avoid_:` synonyms. Project-specific terms only, no implementation detail.
  - The three ADR conditions and the ADR format; a new ADR's number is the highest existing number + 1.
  - Write after every answered round: append to `## Decisions` in `plan.md`, update the glossary and ADRs.
  - Finish when the frontier is empty and the user confirms they share the same understanding.
- **`skills/poe/SKILL.md`**:
  - `argument-hint` and Operating modes: add `grill <task | plan-path>`. It may write `poe/<slug>/plan.md`, `poe/docs/GLOSSARY.md` and `poe/docs/adr/`; it never touches implementation files.
  - Files: show `poe/docs/` next to the task directories. The slug `docs` is reserved. `poe/docs/` (and the existing `poe/trash/`) are never treated as the "active plan" when a mode is run without a path.
  - Plan mode: step 1 also reads `poe/docs/` when it exists. Step 4 becomes: open decisions found → switch to Grill mode with the task; otherwise write the plan in one shot.
  - New Grill mode section:
    1. Do Plan step 1, then read `poe/docs/` and `${CLAUDE_SKILL_DIR}/GRILLING.md`.
    2. If the argument is an existing `plan.md`, load it and grill only its assumptions and open or risky points. Otherwise create a new slug and a `plan.md` containing only `## Decisions`.
    3. Ask a round and stop. After the answers, write as GRILLING.md says.
    4. When the frontier is empty, ask the user to confirm.
    5. Once confirmed, write or update the full plan (Plan steps 2–3; keep `## Decisions`; link any new ADRs), then reply as in Plan step 5 (`Next:` split block).
    6. Copy the logs at the end of the mode, as every other mode does.
  - Split step 4: when `poe/docs/GLOSSARY.md` or relevant ADRs exist, list them in each unit's inputs.
- **`README.md`**: show `grill` usage; one or two lines on when to use `plan` versus `grill`; add `poe/docs/` to the Files tree; change the gitignore advice to ignore `poe/*/logs/` and `poe/*/report.html` but not all of `poe/`, so the shared docs stay in git; credit upstream under References.

Out:
- `phase-worker.md` (the briefs already carry the docs paths), `poe_report.py`, its tests, any flags or config, showing the glossary in the report.
- The other upstream skills (to-spec, wayfinder, etc.).

## Assumptions
- Builds on the current `less_verboosity` branch.
- "Fuzzy" = an open decision that is the user's to make and cannot be settled from the code or sensible defaults. A missing detail with an obvious default is not fuzzy.
- Round questions are terse, per the Output style, but every question keeps its recommended answer.
- `poe/` is relative to the cwd (existing rule).

## Acceptance criteria
- `GRILLING.md` exists, credits upstream with the MIT notice, and covers every item under Scope.
- SKILL.md: `grill` appears in `argument-hint` and in Operating modes; the Grill section has steps 1–6 and points to the Plan steps instead of copying them; Plan step 4 routes fuzzy requests to grilling; `docs` is a reserved slug; Split step 4 mentions the docs inputs.
- README updated as described under Scope.
- `claude plugin validate .` passes.
- `python3 -m unittest discover tests` passes.
- Manual run (see Validation) shows:
  - Clear task + `plan` → no questions, one-shot `plan.md`.
  - Fuzzy task + `plan` → switches to grill rounds.
  - Rounds are numbered, with a recommended answer for each, and no fact questions.
  - `## Decisions` grows each round, and `poe/docs/GLOSSARY.md` is written mid-session, not all at the end.
  - ADRs appear only when all three conditions are met (zero is fine).
  - No full plan is written before the user confirms.
  - `grill <plan.md>` after `/clear` does not re-ask settled points.
  - Every mode ends with the `Next:` block.
  - Nothing is written outside `poe/`.

## Risks
- Plan's fuzzy detection is unreliable (it grills a clear task or skips a fuzzy one). Mitigation: a strict definition of fuzzy; the user can always run `grill` explicitly.
- Question fatigue or trivia. Mitigation: recommended answers, "yes" accepts all, the skip-trivia rule.
- Docs written only at the end (upstream bug). Mitigation: an explicit write step after every round.
- Users who ignore all of `poe/` lose the shared docs. Mitigation: README gitignore note.
- Upstream tools look for `GLOSSARY.md` at the repo root and won't find poe's. Accepted.
- The parent context grows over many rounds. Mitigation: decisions are on disk; `/clear`, then `grill <plan-path>`.
- `plan` and `grill` drift apart. Mitigation: Grill points to the Plan steps instead of copying them.

## Validation
- `claude plugin validate .`
- `python3 -m unittest discover tests`
- Manual: scratch git repo + `claude --plugin-dir <this repo>`:
  1. `/poe:poe plan add a --verbose flag to cli.py` → one-shot plan.
  2. `/poe:poe plan add archiving for old notes` → grill rounds start. Answer 2–3 rounds, mixing "yes" and overrides. After each round check `git status`, `cat poe/docs/GLOSSARY.md` and `cat poe/<slug>/plan.md`.
  3. `/clear`, then `/poe:poe grill poe/<slug>/plan.md` → no re-asks.
  4. `/poe:poe split` → the briefs list `poe/docs/GLOSSARY.md`.
