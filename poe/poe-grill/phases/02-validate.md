# Phase 02: validate

- Depends on: phase 01 verified (all three units).

## Unit 02a: automated + manual validation
- Goal: run plan's Validation; report results against Acceptance criteria.
- Read: `poe/poe-grill/plan.md` (Acceptance criteria, Validation); `skills/poe/GRILLING.md`; `skills/poe/SKILL.md`; `README.md`.
- May change: nothing in repo. Scratch repo under the session scratchpad dir only. Fixes → report, don't apply.
- Steps:
  - `claude plugin validate .`
  - `python3 -m unittest discover tests`
  - Static check: each Acceptance criterion for GRILLING.md / SKILL.md / README → pass/fail with line refs.
  - Manual run (plan Validation 1–4) in scratch git repo with `claude --plugin-dir <repo>`. Use headless `claude -p` (+ `--resume <session>` for follow-up rounds) if it works; otherwise mark the step "needs user" with exact commands. Check after each round: `git status`, `poe/docs/GLOSSARY.md`, `poe/<slug>/plan.md` `## Decisions` growth; no writes outside `poe/`; `Next:` block at end of each mode.
- Non-goals: editing skill/README files; changing tests or `poe_report.py`.
- Done when: every Acceptance criterion marked pass / fail / needs-user with evidence (command + observed output).
- Progress notes: `poe/poe-grill/progress/02a-validate.md`
