# Phase 01: grill question counter

Depends on: none. Single unit; no parallelism (2 small doc edits).

## Unit 01-01: add `Q<k> of ~<N>` counter rule + README mention

Goal
- GRILLING.md and README.md describe the grill question counter per `poe/poe-grill-count/plan.md` (Decisions, Assumptions, Approach).

Inputs (read)
- `poe/poe-grill-count/plan.md`
- `skills/poe/GRILLING.md` (`## Questions`, ~lines 24–38)
- `README.md` Grill bullet (`- **Grill** interviews you...`, ~line 67)
- `poe/docs/GLOSSARY.md`

May change
- `skills/poe/GRILLING.md` (`## Questions` section only)
- `README.md` (Grill bullet only)
- `poe/poe-grill-count/progress/01-01-grill-counter.md`

Non-goals
- `skills/poe/SKILL.md`, decision tree, writes-after-answer, glossary, ADR rules, `poe_report.py`, tests.
- No persisted counter state; no new files.
- No commit.

Edits
- GRILLING.md, after "Ask exactly one question per turn" bullet:
  - Before Q1: estimate N = all open decisions known so far (whole tree, not just frontier), excl. final confirm; `grill <plan-path>` → only the open points being grilled.
  - Prefix every `question`: `Q<k> of ~<N>: `; `~` always shown; header unchanged.
  - After each answer: re-estimate N (asked + still open); show new N on next question. k +1 per question, never resets within a run; new run after `/clear` restarts at Q1.
  - Final "Matches your understanding?" confirm: no prefix, not counted.
- GRILLING.md fallback bullet ("Tool unavailable or call rejected"): plain-text question carries same prefix.
- README Grill bullet: add "each question shows `Q1 of ~N`, an estimate revised as answers add or remove questions".
- Keep terse style of surrounding bullets.

Verification
```sh
grep -n 'of ~' skills/poe/GRILLING.md README.md   # hits in both
python3 -m pytest tests/                          # passes
git diff --stat                                   # only GRILLING.md, README.md
```

Completion criteria
- All plan acceptance criteria except manual run met; grep hits both files; pytest passes; diff limited to allowed files.
- Manual run (user, after execute): `claude --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe`, `/poe:poe grill add archiving for old notes` in scratch repo; ≥3 answers; check prefix, k increments, N revises, confirm unprefixed.

Progress notes
- `poe/poe-grill-count/progress/01-01-grill-counter.md`
