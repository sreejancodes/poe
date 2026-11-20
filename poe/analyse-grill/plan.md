# Plan: grill in analyse mode; analysis-ready grill plans

## Objective
- `analyse` grills the user on open decisions instead of guessing.
- A plan from `grill` on an analysis task is ready for `/poe:poe analyse <plan>` with no hand edits.

## Scope
- In: `skills/poe/SKILL.md`, `skills/poe/GRILLING.md`, `README.md` (Usage + Analysis sections).
- Out: report script, phase-worker agent, catch-up/note modes, tests (no code change).

## Analysis fields (required in an analysis plan)
- Question (overall).
- Data paths.
- Notebook/output path.
- Environment + exact `jupyter` call.
- First analysis (new).

## Approach
- SKILL.md Plan step 2: add `First analysis` to the analysis-task field list.
- SKILL.md Analyse step 1:
  - No plan → as Plan step 4: open decisions → Grill mode with the task; else one-shot plan. Stop for review, `Next:` = `analyse <plan>`.
  - Plan exists, analysis fields missing → look up facts; grill remaining ones (GRILLING.md method, Decisions appended); write fields into plan; continue.
- SKILL.md Analyse step 3: first analysis = plan's `First analysis`; later = user's pick.
- SKILL.md Grill step 5: `Next:` = `analyse <plan>` for analysis-only task; `split <plan>` for coding or mixed (reply line notes `analyse` works after).
- GRILLING.md: short "Analysis tasks" section: analysis task (request is data analysis, or grill entered from `analyse`) → decision tree includes the analysis fields; facts (data location, env, jupyter availability) looked up, not asked.
- README: Grill/Analyse bullets + Analysis "Start" bullet reflect the above.

## Assumptions
- "Analysis task" judged from the request; entering grill from `analyse` always counts.
- Fields already in the plan not re-asked.
- Grill from `analyse` still stops for review (no auto-start), same as current no-plan path.

## Acceptance criteria
- SKILL.md analyse step 1 has both grill paths; grill step 5 has the analyse/split `Next:` rule.
- GRILLING.md names the five analysis fields and the facts-vs-decisions rule for them.
- README matches SKILL.md; no contradicting text left (grep `Next:`, `analyse <task>`, `split`).
- Existing tests still pass: `python3 -m pytest tests -q`.

## Risks
- SKILL.md growth → keep each change to a line or two.
- Installed plugin cache is a copy; change takes effect only after plugin update/reinstall.

## Validation
- Read-through of edited sections for consistency.
- Manual dry run later: `/poe:poe grill <analysis task>` → Next block is `analyse`; `/poe:poe analyse <plan missing fields>` → asks only missing ones.

## Decisions
- `analyse <task>` without plan → grill only if open decisions exist, else one-shot plan (same rule as Plan step 4).
- `analyse <plan-path>` with missing analysis fields (question, data paths, notebook/output path, environment + jupyter call) → look up facts in repo, grill only what remains, write to plan.md, then continue. Avoids worker guessing.
- Analysis plans get a `First analysis` field; grill settles it for analysis tasks, so `analyse <plan>` starts the first analysis without asking. Later analyses unchanged (worker proposals + user pick).
- Grill `Next:` block: analysis-only → `analyse <plan>`; coding or mixed → `split <plan>` (mixed plans still carry analysis fields; reply notes `analyse` works after). Keeps one command to paste.
